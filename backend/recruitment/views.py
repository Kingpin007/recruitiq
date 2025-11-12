from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import (
    Candidate,
    Evaluation,
    JobDescription,
    ProcessingLog,
    StakeholderFeedback,
)
from .serializers import (
    CandidateCreateSerializer,
    CandidateSerializer,
    EvaluationDetailSerializer,
    EvaluationSerializer,
    JobDescriptionSerializer,
    ProcessingLogSerializer,
    ResumeUploadSerializer,
    StakeholderFeedbackSerializer,
)
from .tasks import process_candidate_task


class JobDescriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing job descriptions."""

    queryset = JobDescription.objects.all()
    serializer_class = JobDescriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Only admins can create, update, or delete job descriptions."""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Filter to show only active job descriptions for non-admin users."""
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        return queryset


class CandidateViewSet(viewsets.ModelViewSet):
    """ViewSet for managing candidates."""

    queryset = Candidate.objects.select_related(
        "job_description", "submitted_by"
    ).prefetch_related("resume", "github_profile", "evaluation")
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "create":
            return CandidateCreateSerializer
        return CandidateSerializer

    def get_queryset(self):
        """Filter candidates based on query parameters."""
        queryset = super().get_queryset()

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by job description
        job_desc_id = self.request.query_params.get("job_description")
        if job_desc_id:
            queryset = queryset.filter(job_description_id=job_desc_id)

        # Non-admin users only see their own submissions
        if not self.request.user.is_staff:
            queryset = queryset.filter(submitted_by=self.request.user)

        return queryset.order_by("-created")

    def perform_create(self, serializer):
        """Set submitted_by to current user."""
        serializer.save(submitted_by=self.request.user)

    @action(detail=False, methods=["post"], url_path="upload-resumes")
    def upload_resumes(self, request):
        """
        Upload one or more resumes and create candidate records.
        Accepts up to 10 resumes at once.
        """
        serializer = ResumeUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resumes = serializer.validated_data["resumes"]
        job_description_id = serializer.validated_data["job_description_id"]
        candidate_name = serializer.validated_data.get("candidate_name")
        candidate_email = serializer.validated_data.get("candidate_email")
        candidate_phone = serializer.validated_data.get("candidate_phone", "")
        candidate_linkedin = serializer.validated_data.get("candidate_linkedin", "")

        try:
            job_description = JobDescription.objects.get(
                id=job_description_id, is_active=True
            )
        except JobDescription.DoesNotExist:
            return Response(
                {"error": "Job description not found or inactive."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_candidates = []

        with transaction.atomic():
            for resume_file in resumes:
                # Extract file info
                original_filename = resume_file.name
                file_ext = original_filename.split(".")[-1].lower()

                # Determine candidate info
                # If multiple resumes, try to extract from filename or use generic
                if len(resumes) == 1 and candidate_name:
                    name = candidate_name
                    email = candidate_email or f"candidate_{original_filename}@unknown.com"
                else:
                    # Extract name from filename or use generic
                    name = original_filename.rsplit(".", 1)[0].replace("_", " ").title()
                    email = f"{name.lower().replace(' ', '.')}@unknown.com"

                # Create candidate
                from .models import Candidate, Resume

                candidate = Candidate.objects.create(
                    name=name,
                    email=email,
                    phone=candidate_phone,
                    linkedin_url=candidate_linkedin,
                    job_description=job_description,
                    submitted_by=request.user,
                    status="pending",
                )

                # Create resume record
                Resume.objects.create(
                    candidate=candidate,
                    file=resume_file,
                    original_filename=original_filename,
                    file_type=file_ext,
                )

                created_candidates.append(candidate)

        # Trigger async processing for each candidate
        for candidate in created_candidates:
            task = process_candidate_task.delay(candidate.id)
            candidate.celery_task_id = str(task.id)
            candidate.status = "processing"
            candidate.save(update_fields=["celery_task_id", "status"])

        return Response(
            {
                "message": f"Successfully uploaded {len(created_candidates)} resume(s).",
                "candidates": CandidateSerializer(
                    created_candidates, many=True, context={"request": request}
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="reprocess")
    def reprocess(self, request, pk=None):
        """Reprocess a candidate's evaluation."""
        candidate = self.get_object()

        if candidate.status == "processing":
            return Response(
                {"error": "Candidate is already being processed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Trigger reprocessing
        task = process_candidate_task.delay(candidate.id)
        candidate.celery_task_id = str(task.id)
        candidate.status = "processing"
        candidate.error_message = None
        candidate.save(update_fields=["celery_task_id", "status", "error_message"])

        return Response(
            {
                "message": "Reprocessing initiated.",
                "candidate": CandidateSerializer(candidate, context={"request": request}).data,
            },
            status=status.HTTP_200_OK,
        )


class EvaluationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing evaluations (read-only)."""

    queryset = Evaluation.objects.select_related("candidate").prefetch_related(
        "stakeholder_feedback"
    )
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return detailed serializer for retrieve action."""
        if self.action == "retrieve":
            return EvaluationDetailSerializer
        return EvaluationSerializer

    def get_queryset(self):
        """Filter evaluations based on permissions."""
        queryset = super().get_queryset()

        # Filter by recommendation
        recommendation = self.request.query_params.get("recommendation")
        if recommendation:
            queryset = queryset.filter(recommendation=recommendation)

        # Filter by score range
        min_score = self.request.query_params.get("min_score")
        if min_score:
            queryset = queryset.filter(overall_score__gte=min_score)

        max_score = self.request.query_params.get("max_score")
        if max_score:
            queryset = queryset.filter(overall_score__lte=max_score)

        # Non-admin users only see evaluations for their submitted candidates
        if not self.request.user.is_staff:
            queryset = queryset.filter(candidate__submitted_by=self.request.user)

        return queryset.order_by("-created")


class StakeholderFeedbackViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing stakeholder feedback (read-only)."""

    queryset = StakeholderFeedback.objects.select_related("evaluation__candidate")
    serializer_class = StakeholderFeedbackSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter feedback based on permissions."""
        queryset = super().get_queryset()

        # Filter by evaluation
        evaluation_id = self.request.query_params.get("evaluation")
        if evaluation_id:
            queryset = queryset.filter(evaluation_id=evaluation_id)

        # Non-admin users only see feedback for their candidates
        if not self.request.user.is_staff:
            queryset = queryset.filter(evaluation__candidate__submitted_by=self.request.user)

        return queryset.order_by("-created")


class ProcessingLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing processing logs (read-only)."""

    queryset = ProcessingLog.objects.select_related("candidate")
    serializer_class = ProcessingLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter logs based on candidate."""
        queryset = super().get_queryset()

        # Filter by candidate
        candidate_id = self.request.query_params.get("candidate")
        if candidate_id:
            queryset = queryset.filter(candidate_id=candidate_id)

        # Non-admin users only see logs for their candidates
        if not self.request.user.is_staff:
            queryset = queryset.filter(candidate__submitted_by=self.request.user)

        return queryset.order_by("created")


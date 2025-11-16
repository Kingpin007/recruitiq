import hashlib
import io
import re

from django.db import transaction
from django.http import FileResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import Candidate, Evaluation, JobDescription, ProcessingLog, StakeholderFeedback
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
from .services.pdf_parser import PDFParser


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

    def destroy(self, request, *args, **kwargs):
        """
        Delete a candidate and all associated data.

        Related models like Resume, GitHubProfile, Evaluation, StakeholderFeedback,
        and ProcessingLog are configured with cascading deletes, so removing the
        candidate will clean up the entire graph.
        """
        candidate = self.get_object()

        # Best-effort audit log entry before deletion; if this fails we still
        # continue with the deletion.
        try:
            ProcessingLog.objects.create(
                candidate=candidate,
                stage="manual_delete",
                status="completed",
                message="Candidate manually deleted via API",
                metadata={"deleted_by": getattr(request.user, "id", None)},
            )
        except Exception:
            pass

        return super().destroy(request, *args, **kwargs)

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

        candidates_to_process = set()
        created_candidates = []

        with transaction.atomic():
            for resume_file in resumes:
                # Extract file info
                original_filename = resume_file.name
                file_ext = original_filename.split(".")[-1].lower()

                # Compute a stable hash of the resume file for deduplication.
                # We read the in-memory file into bytes, hash it, then reset
                # the pointer so Django can save it normally later.
                file_content = resume_file.read()
                file_hash = hashlib.sha256(file_content).hexdigest()
                resume_file.seek(0)

                # Try to infer candidate email from the resume content when not
                # explicitly provided.
                inferred_email = None
                try:
                    parser = PDFParser()
                    buffer = io.BytesIO(file_content)

                    if file_ext == "pdf":
                        text = parser.extract_from_pdf(buffer)
                    elif file_ext in ["txt", "text"]:
                        text = parser.extract_from_text(buffer)
                    elif file_ext in ["doc", "docx"]:
                        text = parser.extract_from_docx(buffer)
                    else:
                        text = ""

                    if text:
                        match = re.search(
                            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
                            text,
                        )
                        if match:
                            inferred_email = match.group(0)
                except Exception:
                    # Email inference is a best-effort feature and should not
                    # block uploads if parsing fails for any reason.
                    inferred_email = None

                # Determine candidate info
                # If multiple resumes, try to extract from filename or use generic
                if len(resumes) == 1 and candidate_name:
                    name = candidate_name
                    email = (
                        candidate_email
                        or inferred_email
                        or f"candidate_{original_filename}@unknown.com"
                    )
                else:
                    # Extract name from filename or use generic
                    name = original_filename.rsplit(".", 1)[0].replace("_", " ").title()
                    email = (
                        inferred_email
                        or candidate_email
                        or f"{name.lower().replace(' ', '.')}@unknown.com"
                    )

                from .models import Resume

                # Either fetch an existing candidate by email or create a new one.
                candidate = Candidate.objects.filter(
                    email=email, job_description=job_description
                ).first()

                if candidate:
                    # Update missing or stale fields in a conservative way.
                    updated_fields = []

                    if candidate_name and candidate.name != candidate_name:
                        candidate.name = candidate_name
                        updated_fields.append("name")

                    if candidate_phone and candidate.phone != candidate_phone:
                        candidate.phone = candidate_phone
                        updated_fields.append("phone")

                    if candidate_linkedin and candidate.linkedin_url != candidate_linkedin:
                        candidate.linkedin_url = candidate_linkedin
                        updated_fields.append("linkedin_url")

                    if updated_fields:
                        candidate.save(update_fields=updated_fields)
                else:
                    candidate = Candidate.objects.create(
                        name=name,
                        email=email,
                        phone=candidate_phone,
                        linkedin_url=candidate_linkedin,
                        job_description=job_description,
                        submitted_by=request.user,
                        status="pending",
                    )
                    created_candidates.append(candidate)

                # Create or update resume record tied to this candidate. If
                # the candidate already has a resume and the hash matches, we
                # simply reuse it without creating a new file.
                resume, _ = Resume.objects.get_or_create(
                    candidate=candidate,
                    defaults={
                        "file": resume_file,
                        "original_filename": original_filename,
                        "file_type": file_ext,
                        "file_hash": file_hash,
                    },
                )

                if resume.file_hash != file_hash:
                    resume.file = resume_file
                    resume.original_filename = original_filename
                    resume.file_type = file_ext
                    resume.file_hash = file_hash
                    resume.save(update_fields=["file", "original_filename", "file_type", "file_hash"])

                candidates_to_process.add(candidate.id)

        # Trigger async processing for each unique candidate affected by this upload
        for candidate_id in candidates_to_process:
            candidate = Candidate.objects.get(id=candidate_id)
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

    @action(detail=True, methods=["post"], url_path="set-status")
    def set_status(self, request, pk=None):
        """
        Manually update candidate review status to processed or rejected.

        This is intentionally separate from the automated pipeline statuses
        (pending/processing/completed/failed) so reviewers can clearly indicate
        their decision.
        """
        candidate = self.get_object()
        new_status = request.data.get("status")

        allowed_statuses = {"processed", "rejected"}
        if new_status not in allowed_statuses:
            return Response(
                {"error": f"Invalid status. Allowed values: {', '.join(sorted(allowed_statuses))}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_status = candidate.status
        candidate.status = new_status
        candidate.save(update_fields=["status"])

        # Record audit log for this manual status change.
        try:
            ProcessingLog.objects.create(
                candidate=candidate,
                stage="manual_status_update",
                status="completed",
                message=f"Candidate status updated from {old_status} to {new_status}",
                metadata={
                    "old_status": old_status,
                    "new_status": new_status,
                    "updated_by": getattr(request.user, "id", None),
                },
            )
        except Exception:
            pass

        return Response(
            CandidateSerializer(candidate, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="download-resume")
    def download_resume(self, request, pk=None):
        """
        Stream the candidate's resume file for viewing/downloading.

        The standard Candidate API already exposes the resume file URL, but
        this endpoint provides a convenient, authenticated download.
        """
        candidate = self.get_object()

        if not hasattr(candidate, "resume") or not candidate.resume.file:
            return Response(
                {"error": "Resume not found for this candidate."},
                status=status.HTTP_404_NOT_FOUND,
            )

        resume = candidate.resume
        file_handle = resume.file.open("rb")
        response = FileResponse(
            file_handle,
            as_attachment=True,
            filename=resume.original_filename or resume.file.name,
        )
        return response

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


from rest_framework import serializers

from .models import (
    Candidate,
    Evaluation,
    GitHubProfile,
    JobDescription,
    ProcessingLog,
    Resume,
    StakeholderFeedback,
)


class JobDescriptionSerializer(serializers.ModelSerializer):
    """Serializer for JobDescription model."""

    class Meta:
        model = JobDescription
        fields = [
            "id",
            "title",
            "description",
            "required_skills",
            "nice_to_have_skills",
            "experience_years",
            "is_active",
            "created",
            "modified",
        ]
        read_only_fields = ["id", "created", "modified"]


class ResumeSerializer(serializers.ModelSerializer):
    """Serializer for Resume model."""

    class Meta:
        model = Resume
        fields = [
            "id",
            "file",
            "original_filename",
            "file_type",
            "parsed_text",
            "parsing_error",
            "created",
            "modified",
        ]
        read_only_fields = ["id", "parsed_text", "parsing_error", "created", "modified"]


class GitHubProfileSerializer(serializers.ModelSerializer):
    """Serializer for GitHubProfile model."""

    class Meta:
        model = GitHubProfile
        fields = [
            "id",
            "username",
            "profile_url",
            "repos_data",
            "analysis",
            "last_fetched",
            "fetch_error",
            "created",
            "modified",
        ]
        read_only_fields = [
            "id",
            "repos_data",
            "analysis",
            "last_fetched",
            "fetch_error",
            "created",
            "modified",
        ]


class EvaluationSerializer(serializers.ModelSerializer):
    """Serializer for Evaluation model."""

    class Meta:
        model = Evaluation
        fields = [
            "id",
            "candidate",
            "overall_score",
            "detailed_analysis",
            "recommendation",
            "assessment_document",
            "processing_logs",
            "ai_model_used",
            "processing_time_seconds",
            "created",
            "modified",
        ]
        read_only_fields = [
            "id",
            "overall_score",
            "detailed_analysis",
            "recommendation",
            "assessment_document",
            "processing_logs",
            "ai_model_used",
            "processing_time_seconds",
            "created",
            "modified",
        ]


class StakeholderFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for StakeholderFeedback model."""

    class Meta:
        model = StakeholderFeedback
        fields = [
            "id",
            "evaluation",
            "stakeholder_identifier",
            "stakeholder_name",
            "feedback_type",
            "feedback_text",
            "telegram_message_id",
            "telegram_chat_id",
            "created",
            "modified",
        ]
        read_only_fields = ["id", "created", "modified"]


class ProcessingLogSerializer(serializers.ModelSerializer):
    """Serializer for ProcessingLog model."""

    class Meta:
        model = ProcessingLog
        fields = [
            "id",
            "candidate",
            "stage",
            "status",
            "message",
            "error_message",
            "metadata",
            "duration_seconds",
            "created",
            "modified",
        ]
        read_only_fields = [
            "id",
            "stage",
            "status",
            "message",
            "error_message",
            "metadata",
            "duration_seconds",
            "created",
            "modified",
        ]


class CandidateSerializer(serializers.ModelSerializer):
    """Serializer for Candidate model."""

    resume = ResumeSerializer(read_only=True)
    github_profile = GitHubProfileSerializer(read_only=True)
    evaluation = EvaluationSerializer(read_only=True)
    job_description_title = serializers.CharField(
        source="job_description.title", read_only=True
    )

    class Meta:
        model = Candidate
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "linkedin_url",
            "status",
            "celery_task_id",
            "job_description",
            "job_description_title",
            "submitted_by",
            "error_message",
            "resume",
            "github_profile",
            "evaluation",
            "created",
            "modified",
        ]
        read_only_fields = [
            "id",
            "status",
            "celery_task_id",
            "submitted_by",
            "error_message",
            "created",
            "modified",
        ]


class CandidateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating candidates."""

    # Expose status in the response while preventing clients from setting it
    # directly on creation. The model default ("pending") will be applied,
    # and this field will be serialized as read-only.
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Candidate
        fields = [
            "name",
            "email",
            "phone",
            "linkedin_url",
            "job_description",
            "status",
        ]


class ResumeUploadSerializer(serializers.Serializer):
    """Serializer for resume upload."""

    resumes = serializers.ListField(
        child=serializers.FileField(max_length=100000, allow_empty_file=False),
        max_length=10,
        min_length=1,
    )
    job_description_id = serializers.IntegerField()
    candidate_name = serializers.CharField(max_length=255, required=False)
    candidate_email = serializers.EmailField(required=False)
    candidate_phone = serializers.CharField(max_length=50, required=False, allow_blank=True)
    candidate_linkedin = serializers.URLField(required=False, allow_blank=True)

    def validate_resumes(self, value):
        """Validate uploaded resume files."""
        if len(value) > 10:
            raise serializers.ValidationError("Maximum 10 resumes can be uploaded at once.")

        for resume_file in value:
            # Check file extension
            allowed_extensions = [".pdf", ".txt", ".doc", ".docx"]
            ext = resume_file.name.split(".")[-1].lower()
            if f".{ext}" not in allowed_extensions:
                raise serializers.ValidationError(
                    f"Invalid file type: {resume_file.name}. Allowed types: PDF, TXT, DOC, DOCX"
                )

            # Check file size (10MB max)
            if resume_file.size > 10 * 1024 * 1024:
                raise serializers.ValidationError(
                    f"File too large: {resume_file.name}. Maximum size is 10MB."
                )

        return value

    def validate_job_description_id(self, value):
        """Validate job description exists and is active."""
        try:
            job_desc = JobDescription.objects.get(id=value, is_active=True)
        except JobDescription.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive job description.")
        return value


class EvaluationDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Evaluation with related data."""

    candidate = CandidateSerializer(read_only=True)
    stakeholder_feedback = StakeholderFeedbackSerializer(many=True, read_only=True)

    class Meta:
        model = Evaluation
        fields = [
            "id",
            "candidate",
            "overall_score",
            "detailed_analysis",
            "recommendation",
            "assessment_document",
            "processing_logs",
            "ai_model_used",
            "processing_time_seconds",
            "stakeholder_feedback",
            "created",
            "modified",
        ]
        read_only_fields = [
            "id",
            "candidate",
            "overall_score",
            "detailed_analysis",
            "recommendation",
            "assessment_document",
            "processing_logs",
            "ai_model_used",
            "processing_time_seconds",
            "stakeholder_feedback",
            "created",
            "modified",
        ]


from django.conf import settings
from django.db import models

from common.models import IndexedTimeStampedModel


class JobDescription(IndexedTimeStampedModel):
    """Stores job requirements and criteria for candidate evaluation."""

    title = models.CharField(max_length=255)
    description = models.TextField()
    required_skills = models.JSONField(
        default=list, help_text="List of required skills for the position"
    )
    nice_to_have_skills = models.JSONField(
        default=list, help_text="Optional skills that are beneficial"
    )
    experience_years = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created"]
        verbose_name = "Job Description"
        verbose_name_plural = "Job Descriptions"

    def __str__(self):
        return self.title


class Candidate(IndexedTimeStampedModel):
    """Tracks candidate information and processing status."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    celery_task_id = models.CharField(max_length=255, blank=True, null=True)
    job_description = models.ForeignKey(
        JobDescription, on_delete=models.CASCADE, related_name="candidates"
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="submitted_candidates",
    )
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-created"]
        verbose_name = "Candidate"
        verbose_name_plural = "Candidates"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["status"]),
            models.Index(fields=["celery_task_id"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.email})"


class Resume(IndexedTimeStampedModel):
    """Stores uploaded resume files and extracted text."""

    candidate = models.OneToOneField(
        Candidate, on_delete=models.CASCADE, related_name="resume"
    )
    file = models.FileField(upload_to="resumes/%Y/%m/%d/")
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10)  # pdf, txt, docx
    parsed_text = models.TextField(blank=True, null=True)
    parsing_error = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Resume"
        verbose_name_plural = "Resumes"

    def __str__(self):
        return f"Resume for {self.candidate.name}"


class GitHubProfile(IndexedTimeStampedModel):
    """Caches GitHub profile data for candidates."""

    candidate = models.OneToOneField(
        Candidate, on_delete=models.CASCADE, related_name="github_profile"
    )
    username = models.CharField(max_length=255)
    profile_url = models.URLField()
    repos_data = models.JSONField(
        default=dict, help_text="Cached repository data from GitHub API"
    )
    analysis = models.JSONField(
        default=dict, help_text="Computed metrics and analysis"
    )
    last_fetched = models.DateTimeField(auto_now=True)
    fetch_error = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "GitHub Profile"
        verbose_name_plural = "GitHub Profiles"
        indexes = [
            models.Index(fields=["username"]),
        ]

    def __str__(self):
        return f"GitHub: {self.username}"


class Evaluation(IndexedTimeStampedModel):
    """Stores AI-generated candidate assessments."""

    RECOMMENDATION_CHOICES = [
        ("interview", "Interview"),
        ("decline", "Decline"),
    ]

    candidate = models.OneToOneField(
        Candidate, on_delete=models.CASCADE, related_name="evaluation"
    )
    overall_score = models.IntegerField(
        help_text="Overall fit score from 1-10"
    )  # 1-10
    detailed_analysis = models.JSONField(
        default=dict,
        help_text="Detailed breakdown including skill matches, strengths, weaknesses",
    )
    recommendation = models.CharField(
        max_length=20, choices=RECOMMENDATION_CHOICES, default="decline"
    )
    assessment_document = models.FileField(
        upload_to="assessments/%Y/%m/%d/", blank=True, null=True
    )
    processing_logs = models.JSONField(
        default=list, help_text="Log of processing steps and decisions"
    )
    ai_model_used = models.CharField(max_length=100, default="gpt-4")
    processing_time_seconds = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["-created"]
        verbose_name = "Evaluation"
        verbose_name_plural = "Evaluations"
        indexes = [
            models.Index(fields=["overall_score"]),
            models.Index(fields=["recommendation"]),
        ]

    def __str__(self):
        return f"Evaluation for {self.candidate.name} (Score: {self.overall_score})"


class StakeholderFeedback(IndexedTimeStampedModel):
    """Tracks feedback from hiring team via Telegram."""

    FEEDBACK_TYPE_CHOICES = [
        ("approve", "Approve"),
        ("reject", "Reject"),
        ("comment", "Comment"),
    ]

    evaluation = models.ForeignKey(
        Evaluation, on_delete=models.CASCADE, related_name="stakeholder_feedback"
    )
    stakeholder_identifier = models.CharField(
        max_length=255, help_text="Telegram user ID or identifier"
    )
    stakeholder_name = models.CharField(max_length=255, blank=True, null=True)
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPE_CHOICES)
    feedback_text = models.TextField(blank=True, null=True)
    telegram_message_id = models.CharField(max_length=255, unique=True)
    telegram_chat_id = models.CharField(max_length=255)

    class Meta:
        ordering = ["-created"]
        verbose_name = "Stakeholder Feedback"
        verbose_name_plural = "Stakeholder Feedback"
        indexes = [
            models.Index(fields=["telegram_message_id"]),
            models.Index(fields=["stakeholder_identifier"]),
        ]

    def __str__(self):
        return f"Feedback from {self.stakeholder_name or self.stakeholder_identifier}"


class ProcessingLog(IndexedTimeStampedModel):
    """Audit trail for candidate processing pipeline."""

    STATUS_CHOICES = [
        ("started", "Started"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("skipped", "Skipped"),
    ]

    candidate = models.ForeignKey(
        Candidate, on_delete=models.CASCADE, related_name="processing_logs"
    )
    stage = models.CharField(
        max_length=100, help_text="Processing stage name (e.g., resume_parsing)"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    message = models.TextField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    metadata = models.JSONField(
        default=dict, help_text="Additional context and data for this stage"
    )
    duration_seconds = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["created"]
        verbose_name = "Processing Log"
        verbose_name_plural = "Processing Logs"
        indexes = [
            models.Index(fields=["candidate", "stage"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.candidate.name} - {self.stage} ({self.status})"


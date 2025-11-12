from django.contrib import admin

from .models import (
    Candidate,
    Evaluation,
    GitHubProfile,
    JobDescription,
    ProcessingLog,
    Resume,
    StakeholderFeedback,
)


@admin.register(JobDescription)
class JobDescriptionAdmin(admin.ModelAdmin):
    list_display = ["title", "experience_years", "is_active", "created"]
    list_filter = ["is_active", "created"]
    search_fields = ["title", "description"]
    readonly_fields = ["created", "modified"]


class ResumeInline(admin.StackedInline):
    model = Resume
    extra = 0
    readonly_fields = ["original_filename", "file_type", "parsed_text"]


class GitHubProfileInline(admin.StackedInline):
    model = GitHubProfile
    extra = 0
    readonly_fields = ["username", "profile_url", "repos_data", "analysis"]


class EvaluationInline(admin.StackedInline):
    model = Evaluation
    extra = 0
    readonly_fields = ["overall_score", "recommendation", "detailed_analysis"]


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "status", "job_description", "created"]
    list_filter = ["status", "created", "job_description"]
    search_fields = ["name", "email"]
    readonly_fields = ["celery_task_id", "created", "modified"]
    inlines = [ResumeInline, GitHubProfileInline, EvaluationInline]


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ["candidate", "original_filename", "file_type", "created"]
    list_filter = ["file_type", "created"]
    search_fields = ["candidate__name", "original_filename"]
    readonly_fields = ["created", "modified"]


@admin.register(GitHubProfile)
class GitHubProfileAdmin(admin.ModelAdmin):
    list_display = ["candidate", "username", "last_fetched"]
    search_fields = ["candidate__name", "username"]
    readonly_fields = ["last_fetched", "created", "modified"]


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = [
        "candidate",
        "overall_score",
        "recommendation",
        "ai_model_used",
        "created",
    ]
    list_filter = ["recommendation", "overall_score", "created"]
    search_fields = ["candidate__name"]
    readonly_fields = ["processing_time_seconds", "created", "modified"]


@admin.register(StakeholderFeedback)
class StakeholderFeedbackAdmin(admin.ModelAdmin):
    list_display = [
        "evaluation",
        "stakeholder_name",
        "feedback_type",
        "created",
    ]
    list_filter = ["feedback_type", "created"]
    search_fields = ["stakeholder_name", "evaluation__candidate__name"]
    readonly_fields = ["telegram_message_id", "created", "modified"]


@admin.register(ProcessingLog)
class ProcessingLogAdmin(admin.ModelAdmin):
    list_display = ["candidate", "stage", "status", "duration_seconds", "created"]
    list_filter = ["status", "stage", "created"]
    search_fields = ["candidate__name", "stage"]
    readonly_fields = ["created", "modified"]


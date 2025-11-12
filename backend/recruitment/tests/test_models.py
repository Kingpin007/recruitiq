import pytest
from django.contrib.auth import get_user_model
from model_bakery import baker

from recruitment.models import (
    Candidate,
    Evaluation,
    GitHubProfile,
    JobDescription,
    ProcessingLog,
    Resume,
    StakeholderFeedback,
)

User = get_user_model()


@pytest.mark.django_db
class TestJobDescription:
    def test_create_job_description(self):
        job = baker.make(
            JobDescription,
            title="Senior Python Developer",
            description="Looking for an experienced Python developer",
            required_skills=["Python", "Django", "PostgreSQL"],
            experience_years=5,
        )

        assert job.title == "Senior Python Developer"
        assert "Python" in job.required_skills
        assert job.experience_years == 5
        assert str(job) == "Senior Python Developer"

    def test_job_description_ordering(self):
        job1 = baker.make(JobDescription, title="Job 1")
        job2 = baker.make(JobDescription, title="Job 2")

        jobs = JobDescription.objects.all()
        assert jobs[0] == job2  # Most recent first


@pytest.mark.django_db
class TestCandidate:
    def test_create_candidate(self):
        user = baker.make(User)
        job = baker.make(JobDescription)
        candidate = baker.make(
            Candidate,
            name="John Doe",
            email="john@example.com",
            job_description=job,
            submitted_by=user,
            status="pending",
        )

        assert candidate.name == "John Doe"
        assert candidate.status == "pending"
        assert candidate.job_description == job
        assert str(candidate) == "John Doe (john@example.com)"

    def test_candidate_status_choices(self):
        candidate = baker.make(Candidate)

        # Test valid status changes
        for status in ["pending", "processing", "completed", "failed"]:
            candidate.status = status
            candidate.save()
            assert candidate.status == status


@pytest.mark.django_db
class TestResume:
    def test_create_resume(self):
        candidate = baker.make(Candidate)
        resume = baker.make(
            Resume, candidate=candidate, original_filename="resume.pdf", file_type="pdf"
        )

        assert resume.candidate == candidate
        assert resume.file_type == "pdf"
        assert str(resume) == f"Resume for {candidate.name}"


@pytest.mark.django_db
class TestGitHubProfile:
    def test_create_github_profile(self):
        candidate = baker.make(Candidate)
        profile = baker.make(
            GitHubProfile,
            candidate=candidate,
            username="johndoe",
            profile_url="https://github.com/johndoe",
            repos_data={"repos": []},
            analysis={"total_repos": 10},
        )

        assert profile.username == "johndoe"
        assert profile.analysis["total_repos"] == 10
        assert str(profile) == "GitHub: johndoe"


@pytest.mark.django_db
class TestEvaluation:
    def test_create_evaluation(self):
        candidate = baker.make(Candidate)
        evaluation = baker.make(
            Evaluation,
            candidate=candidate,
            overall_score=8,
            recommendation="interview",
            detailed_analysis={"strengths": ["Strong Python skills"]},
        )

        assert evaluation.overall_score == 8
        assert evaluation.recommendation == "interview"
        assert "strengths" in evaluation.detailed_analysis
        assert "Strong Python skills" in evaluation.detailed_analysis["strengths"]

    def test_evaluation_score_range(self):
        candidate = baker.make(Candidate)
        evaluation = baker.make(Evaluation, candidate=candidate, overall_score=10)

        assert 1 <= evaluation.overall_score <= 10


@pytest.mark.django_db
class TestStakeholderFeedback:
    def test_create_feedback(self):
        evaluation = baker.make(Evaluation)
        feedback = baker.make(
            StakeholderFeedback,
            evaluation=evaluation,
            stakeholder_identifier="123456",
            feedback_type="approve",
            telegram_message_id="msg_123",
        )

        assert feedback.feedback_type == "approve"
        assert feedback.evaluation == evaluation


@pytest.mark.django_db
class TestProcessingLog:
    def test_create_processing_log(self):
        candidate = baker.make(Candidate)
        log = baker.make(
            ProcessingLog,
            candidate=candidate,
            stage="resume_parsing",
            status="completed",
            message="Successfully parsed resume",
        )

        assert log.stage == "resume_parsing"
        assert log.status == "completed"
        assert str(log) == f"{candidate.name} - resume_parsing (completed)"

    def test_processing_log_ordering(self):
        candidate = baker.make(Candidate)
        log1 = baker.make(ProcessingLog, candidate=candidate, stage="stage_1")
        log2 = baker.make(ProcessingLog, candidate=candidate, stage="stage_2")

        logs = ProcessingLog.objects.filter(candidate=candidate)
        assert logs[0] == log1  # Oldest first


@pytest.mark.django_db
class TestCandidateRelationships:
    def test_candidate_with_all_relationships(self):
        user = baker.make(User)
        job = baker.make(JobDescription)
        candidate = baker.make(Candidate, job_description=job, submitted_by=user)
        resume = baker.make(Resume, candidate=candidate)
        github = baker.make(GitHubProfile, candidate=candidate)
        evaluation = baker.make(Evaluation, candidate=candidate)
        log = baker.make(ProcessingLog, candidate=candidate)

        # Test relationships
        assert candidate.resume == resume
        assert candidate.github_profile == github
        assert candidate.evaluation == evaluation
        assert candidate.processing_logs.count() == 1
        assert candidate.processing_logs.first() == log


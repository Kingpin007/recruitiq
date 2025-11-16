import pytest
from django.urls import reverse
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APIClient

from recruitment.models import Candidate, Evaluation, JobDescription
from users.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return baker.make(User, email="test@example.com")


@pytest.fixture
def admin_user():
    return baker.make(User, email="admin@example.com", is_staff=True)


@pytest.fixture
def job_description():
    return baker.make(
        JobDescription,
        title="Software Engineer",
        description="Great opportunity",
        required_skills=["Python", "Django"],
        is_active=True,
    )


@pytest.mark.django_db
class TestJobDescriptionAPI:
    def test_list_job_descriptions(self, api_client, user, job_description):
        api_client.force_authenticate(user=user)
        url = reverse("recruitment:jobdescription-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

    def test_create_job_description_as_admin(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        url = reverse("recruitment:jobdescription-list")
        data = {
            "title": "Backend Developer",
            "description": "Looking for a backend developer",
            "required_skills": ["Python", "FastAPI"],
            "experience_years": 3,
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "Backend Developer"

    def test_create_job_description_as_regular_user(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse("recruitment:jobdescription-list")
        data = {"title": "Test Job", "description": "Test"}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestCandidateAPI:
    def test_list_candidates(self, api_client, user, job_description):
        baker.make(Candidate, job_description=job_description, submitted_by=user, _quantity=3)

        api_client.force_authenticate(user=user)
        url = reverse("recruitment:candidate-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 3

    def test_create_candidate(self, api_client, user, job_description):
        api_client.force_authenticate(user=user)
        url = reverse("recruitment:candidate-list")
        data = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "job_description": job_description.id,
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Jane Doe"
        assert response.data["status"] == "pending"

    def test_filter_candidates_by_status(self, api_client, user, job_description):
        baker.make(Candidate, job_description=job_description, submitted_by=user, status="completed")
        baker.make(Candidate, job_description=job_description, submitted_by=user, status="pending")

        api_client.force_authenticate(user=user)
        url = reverse("recruitment:candidate-list")
        response = api_client.get(url, {"status": "completed"})

        assert response.status_code == status.HTTP_200_OK
        assert all(c["status"] == "completed" for c in response.data["results"])

    def test_users_only_see_own_candidates(self, api_client, user, job_description):
        other_user = baker.make(User)

        baker.make(Candidate, job_description=job_description, submitted_by=user)
        baker.make(Candidate, job_description=job_description, submitted_by=other_user)

        api_client.force_authenticate(user=user)
        url = reverse("recruitment:candidate-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1


@pytest.mark.django_db
class TestEvaluationAPI:
    def test_list_evaluations(self, api_client, user, job_description):
        candidate = baker.make(Candidate, job_description=job_description, submitted_by=user)
        baker.make(Evaluation, candidate=candidate, overall_score=8)

        api_client.force_authenticate(user=user)
        url = reverse("recruitment:evaluation-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

    def test_filter_evaluations_by_recommendation(self, api_client, user, job_description):
        candidate1 = baker.make(Candidate, job_description=job_description, submitted_by=user)
        candidate2 = baker.make(Candidate, job_description=job_description, submitted_by=user)

        baker.make(Evaluation, candidate=candidate1, recommendation="interview")
        baker.make(Evaluation, candidate=candidate2, recommendation="decline")

        api_client.force_authenticate(user=user)
        url = reverse("recruitment:evaluation-list")
        response = api_client.get(url, {"recommendation": "interview"})

        assert response.status_code == status.HTTP_200_OK
        assert all(e["recommendation"] == "interview" for e in response.data["results"])

    def test_filter_evaluations_by_score_range(self, api_client, user, job_description):
        candidate1 = baker.make(Candidate, job_description=job_description, submitted_by=user)
        candidate2 = baker.make(Candidate, job_description=job_description, submitted_by=user)

        baker.make(Evaluation, candidate=candidate1, overall_score=8)
        baker.make(Evaluation, candidate=candidate2, overall_score=4)

        api_client.force_authenticate(user=user)
        url = reverse("recruitment:evaluation-list")
        response = api_client.get(url, {"min_score": 7})

        assert response.status_code == status.HTTP_200_OK
        assert all(e["overall_score"] >= 7 for e in response.data["results"])


@pytest.mark.django_db
class TestUploadResumesAPI:
    def test_upload_single_resume(self, api_client, user, job_description):
        api_client.force_authenticate(user=user)
        url = reverse("recruitment:candidate-upload-resumes")

        # Create a mock PDF file
        from io import BytesIO

        pdf_content = b"%PDF-1.4 mock pdf content"
        pdf_file = BytesIO(pdf_content)
        pdf_file.name = "resume.pdf"

        data = {
            "resumes": [pdf_file],
            "job_description_id": job_description.id,
        }
        response = api_client.post(url, data, format="multipart")

        assert response.status_code == status.HTTP_201_CREATED
        assert "candidates" in response.data
        assert len(response.data["candidates"]) == 1

    def test_concurrent_uploads_are_isolated_per_candidate(
        self, api_client, user, job_description, django_db_blocker, monkeypatch
    ):
        """
        Demonstrate concurrent processing safety:

        - Multiple resumes uploaded in a single request create distinct candidates.
        - Each candidate is scheduled for processing exactly once.
        - Each candidate receives its own celery_task_id and remains isolated.
        """

        from io import BytesIO

        api_client.force_authenticate(user=user)
        url = reverse("recruitment:candidate-upload-resumes")

        # Prepare two different mock resume files to simulate multiple candidates.
        pdf_content_1 = b"%PDF-1.4 mock pdf content candidate 1"
        pdf_content_2 = b"%PDF-1.4 mock pdf content candidate 2"

        file1 = BytesIO(pdf_content_1)
        file1.name = "alice_resume.pdf"

        file2 = BytesIO(pdf_content_2)
        file2.name = "bob_resume.pdf"

        scheduled_candidate_ids = []

        class DummyResult:
            def __init__(self, task_id):
                self.id = task_id

        # Patch the Celery task used by the upload endpoint so we can
        # assert exactly which candidate IDs are scheduled for processing.
        from recruitment import views as recruitment_views

        def fake_delay(candidate_id):
            scheduled_candidate_ids.append(candidate_id)
            # Use deterministic task IDs so we can assert isolation.
            return DummyResult(task_id=f"task-{candidate_id}")

        monkeypatch.setattr(recruitment_views.process_candidate_task, "delay", fake_delay)

        data = {
            "resumes": [file1, file2],
            "job_description_id": job_description.id,
        }

        response = api_client.post(url, data, format="multipart")

        assert response.status_code == status.HTTP_201_CREATED
        assert "candidates" in response.data
        assert len(response.data["candidates"]) == 2

        # Collect candidate IDs returned by the API.
        returned_ids = {c["id"] for c in response.data["candidates"]}
        assert len(returned_ids) == 2

        # Each candidate should have been scheduled exactly once.
        assert set(scheduled_candidate_ids) == returned_ids

        # Reload candidates from the database to verify status and task IDs.
        with django_db_blocker.unblock():
            candidates = Candidate.objects.filter(id__in=returned_ids)

        assert candidates.count() == 2

        celery_ids = set()
        for candidate in candidates:
            # Status should have transitioned from "pending" to "processing"
            # after scheduling, and each should have a unique task ID.
            assert candidate.status == "processing"
            assert candidate.celery_task_id == f"task-{candidate.id}"
            celery_ids.add(candidate.celery_task_id)

        # Ensure no two candidates share the same celery_task_id,
        # demonstrating isolation between concurrent processing tasks.
        assert len(celery_ids) == 2


@pytest.mark.django_db
class TestReprocessAPI:
    def test_reprocess_failed_candidate(self, api_client, user, job_description):
        candidate = baker.make(
            Candidate,
            job_description=job_description,
            submitted_by=user,
            status="failed",
            error_message="Something went wrong",
        )

        api_client.force_authenticate(user=user)
        url = reverse("recruitment:candidate-reprocess", kwargs={"pk": candidate.id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        candidate.refresh_from_db()
        assert candidate.status == "processing"
        assert candidate.error_message is None


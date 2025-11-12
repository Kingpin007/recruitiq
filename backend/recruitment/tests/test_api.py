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


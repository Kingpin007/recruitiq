from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CandidateViewSet,
    EvaluationViewSet,
    JobDescriptionViewSet,
    ProcessingLogViewSet,
    StakeholderFeedbackViewSet,
)

app_name = "recruitment"

router = DefaultRouter()
router.register(r"job-descriptions", JobDescriptionViewSet, basename="jobdescription")
router.register(r"candidates", CandidateViewSet, basename="candidate")
router.register(r"evaluations", EvaluationViewSet, basename="evaluation")
router.register(r"stakeholder-feedback", StakeholderFeedbackViewSet, basename="stakeholder-feedback")
router.register(r"processing-logs", ProcessingLogViewSet, basename="processing-log")

urlpatterns = [
    path("", include(router.urls)),
]


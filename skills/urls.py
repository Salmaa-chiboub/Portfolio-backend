from rest_framework.routers import DefaultRouter

from .views import SkillReferenceViewSet, SkillViewSet

router = DefaultRouter()
router.register(r"references", SkillReferenceViewSet, basename="skillreference")
# Mount SkillViewSet at the router root so when included at 'api/skills/' it becomes '/api/skills/'
router.register(r"", SkillViewSet, basename="skill")

urlpatterns = router.urls

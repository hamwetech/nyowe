from rest_framework.routers import DefaultRouter
from dashboard.members.views import DashBoardViewSet


router = DefaultRouter()
router.register(r'data', DashBoardViewSet, base_name='insights')

urlpatterns = router.urls

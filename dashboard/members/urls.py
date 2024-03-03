
from django.urls import re_path as url, include
from rest_framework.routers import DefaultRouter
from dashboard.members.views import DashBoardViewSet


app_name = 'dashboards'

router = DefaultRouter()
router.register('insights', DashBoardViewSet)

urlpatterns = [
    url(r'^/', include(router.urls))
]

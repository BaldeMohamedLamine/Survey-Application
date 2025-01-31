from __future__ import annotations

from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from .api_views import ResponseViewSet
from .api_views import SurveyViewSet

router = DefaultRouter()
router.register(r'surveys', SurveyViewSet, basename='survey')
router.register(r'responses', ResponseViewSet, basename='response')

urlpatterns = [
    path('', include(router.urls)),
]

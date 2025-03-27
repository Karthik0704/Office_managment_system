from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CameraViewSet, MotionEventViewSet, PersonDetectionViewSet,
    MonitoringZoneViewSet, ZoneActivityViewSet, test_camera_frame, public_test,
    camera_viewer  # Add this import
)

router = DefaultRouter()
router.register(r'cameras', CameraViewSet)
router.register(r'motion-events', MotionEventViewSet)
router.register(r'person-detections', PersonDetectionViewSet)
router.register(r'zones', MonitoringZoneViewSet)
router.register(r'zone-activities', ZoneActivityViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('test-frame/', test_camera_frame, name='test_camera_frame'),
    path('public-test/', public_test, name='public_test'),
    path('viewer/', camera_viewer, name='camera_viewer'),
]
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from rest_framework.permissions import AllowAny
import time
from django.shortcuts import render
from .models import Camera, MotionEvent, PersonDetection, MonitoringZone, ZoneActivity
from .serializers import (
    CameraSerializer, MotionEventSerializer, PersonDetectionSerializer,
    MonitoringZoneSerializer, ZoneActivitySerializer
)
from .utils import generate_dummy_frame, detect_motion
from .camera_service import camera_service  # Added import

class CameraViewSet(viewsets.ModelViewSet):
    queryset = Camera.objects.all()
    serializer_class = CameraSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'location', 'ip_address']
    ordering_fields = ['name', 'location', 'status', 'created_at']

    @action(detail=True, methods=['get'])
    def motion_events(self, request, pk=None):
        camera = self.get_object()
        events = MotionEvent.objects.filter(camera=camera).order_by('-timestamp')

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if start_date:
            events = events.filter(timestamp__gte=start_date)
        if end_date:
            events = events.filter(timestamp__lte=end_date)

        page = self.paginate_queryset(events)
        if page is not None:
            serializer = MotionEventSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = MotionEventSerializer(events, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def stream_frame(self, request, pk=None):
        """Get a single frame from the camera stream (simulated)."""
        camera = self.get_object()
        frame_data = generate_dummy_frame(camera.name)
        return Response(frame_data)

    @action(detail=True, methods=['get'])
    def simulate_motion(self, request, pk=None):
        """Simulate motion detection with multiple frames."""
        camera = self.get_object()
        frames = []
        motion_data = None
        prev_frame = None

        for i in range(5):
            curr_frame = generate_dummy_frame(camera.name)
            frames.append(curr_frame)

            if prev_frame:
                motion_detected, motion_info = detect_motion(prev_frame, curr_frame)
                if motion_detected and motion_info:
                    motion_data = {
                        'camera_id': camera.id,
                        'camera_name': camera.name,
                        'timestamp': curr_frame['timestamp'],
                        'motion_frame': motion_info['frame'],
                        'bounding_box': motion_info['bounding_box'],
                        'confidence': motion_info['confidence']
                    }
                    break

            prev_frame = curr_frame
            time.sleep(0.2)

        return Response({
            'camera': CameraSerializer(camera).data,
            'frames': frames,
            'motion_detected': motion_data is not None,
            'motion_data': motion_data
        })

    @action(detail=True, methods=['post'])
    def start_stream(self, request, pk=None):
        """Start streaming from a camera."""
        camera = self.get_object()
        success = camera_service.start_camera_stream(camera.id)
        return Response({
            'success': success,
            'message': 'Stream started' if success else 'Failed to start stream'
        })

    @action(detail=True, methods=['post'])
    def stop_stream(self, request, pk=None):
        """Stop streaming from a camera."""
        camera = self.get_object()
        success = camera_service.stop_camera_stream(camera.id)
        return Response({
            'success': success,
            'message': 'Stream stopped' if success else 'Failed to stop stream'
        })

    @action(detail=True, methods=['get'])
    def get_frame(self, request, pk=None):
        """Get the latest frame from a camera."""
        camera = self.get_object()
        frame_data = camera_service.get_latest_frame(camera.id)
        if not frame_data:
            return Response({
                'success': False,
                'message': 'No frame available'
            }, status=404)
        
        return Response({
            'success': True,
            'camera_id': camera.id,
            'camera_name': camera.name,
            'frame': frame_data['frame'],
            'timestamp': frame_data['timestamp']
        })


class MotionEventViewSet(viewsets.ModelViewSet):
    queryset = MotionEvent.objects.all().order_by('-timestamp')
    serializer_class = MotionEventSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['camera', 'is_reviewed']
    search_fields = ['camera__name', 'notes']
    ordering_fields = ['timestamp', 'confidence', 'created_at']

    @action(detail=True, methods=['post'])
    def mark_reviewed(self, request, pk=None):
        event = self.get_object()
        event.is_reviewed = True
        event.notes = request.data.get('notes', event.notes)
        event.save()
        serializer = MotionEventSerializer(event)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def person_detections(self, request, pk=None):
        event = self.get_object()
        detections = PersonDetection.objects.filter(motion_event=event)
        serializer = PersonDetectionSerializer(detections, many=True)
        return Response(serializer.data)


class PersonDetectionViewSet(viewsets.ModelViewSet):
    queryset = PersonDetection.objects.all().order_by('-timestamp')
    serializer_class = PersonDetectionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['motion_event', 'employee']
    search_fields = ['employee__user__first_name', 'employee__user__last_name']
    ordering_fields = ['timestamp', 'confidence']


class MonitoringZoneViewSet(viewsets.ModelViewSet):
    queryset = MonitoringZone.objects.all()
    serializer_class = MonitoringZoneSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'zone_type']
    ordering_fields = ['name', 'zone_type', 'created_at']

    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        zone = self.get_object()
        activities = ZoneActivity.objects.filter(zone=zone).order_by('-timestamp')

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if start_date:
            activities = activities.filter(timestamp__gte=start_date)
        if end_date:
            activities = activities.filter(timestamp__lte=end_date)

        page = self.paginate_queryset(activities)
        if page is not None:
            serializer = ZoneActivitySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ZoneActivitySerializer(activities, many=True)
        return Response(serializer.data)


class ZoneActivityViewSet(viewsets.ModelViewSet):
    queryset = ZoneActivity.objects.all().order_by('-timestamp')
    serializer_class = ZoneActivitySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['zone', 'employee', 'activity_type', 'is_authorized']
    search_fields = ['employee__user__first_name', 'employee__user__last_name', 'zone__name']
    ordering_fields = ['timestamp', 'activity_type']

    @action(detail=False, methods=['post'])
    def record_activity(self, request):
        serializer = ZoneActivitySerializer(data=request.data)
        if serializer.is_valid():
            if 'timestamp' not in request.data:
                serializer.validated_data['timestamp'] = timezone.now()

            zone = serializer.validated_data['zone']
            employee = serializer.validated_data['employee']

            is_authorized = employee in zone.authorized_employees.all()
            serializer.validated_data['is_authorized'] = is_authorized

            activity = serializer.save()
            return Response(ZoneActivitySerializer(activity).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def test_camera_frame(request):
    """Get a test camera frame without authentication."""
    camera_name = request.query_params.get('name', 'Test Camera')
    frame_data = generate_dummy_frame(camera_name)
    return Response(frame_data)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_test(request):
    """A simple test view that doesn't require authentication."""
    return Response({
        'message': 'This is a public test endpoint that works without authentication.',
        'status': 'success'
    })

def camera_viewer(request):
    """Render the camera viewer page."""
    return render(request, 'monitoring/camera_viewer.html')
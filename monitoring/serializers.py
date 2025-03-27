from rest_framework import serializers
from .models import Camera, MotionEvent, PersonDetection, MonitoringZone, ZoneActivity

class CameraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Camera
        fields = ['id', 'name', 'location', 'ip_address', 'port', 'username', 
                  'password', 'status', 'description', 'stream_url', 
                  'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }

class MotionEventSerializer(serializers.ModelSerializer):
    camera_name = serializers.ReadOnlyField(source='camera.name')
    
    class Meta:
        model = MotionEvent
        fields = ['id', 'camera', 'camera_name', 'timestamp', 'snapshot', 
                  'video_clip', 'confidence', 'is_reviewed', 'notes', 'created_at']

class PersonDetectionSerializer(serializers.ModelSerializer):
    employee_name = serializers.ReadOnlyField(source='employee.user.get_full_name')
    
    class Meta:
        model = PersonDetection
        fields = ['id', 'motion_event', 'employee', 'employee_name', 'timestamp', 
                  'confidence', 'face_image', 'bounding_box']

class MonitoringZoneSerializer(serializers.ModelSerializer):
    cameras_detail = CameraSerializer(source='cameras', many=True, read_only=True)
    
    class Meta:
        model = MonitoringZone
        fields = ['id', 'name', 'zone_type', 'cameras', 'cameras_detail', 
                  'description', 'authorized_employees', 'created_at', 'updated_at']

class ZoneActivitySerializer(serializers.ModelSerializer):
    zone_name = serializers.ReadOnlyField(source='zone.name')
    employee_name = serializers.ReadOnlyField(source='employee.user.get_full_name')
    camera_name = serializers.ReadOnlyField(source='camera.name')
    
    class Meta:
        model = ZoneActivity
        fields = ['id', 'zone', 'zone_name', 'employee', 'employee_name', 
                  'timestamp', 'activity_type', 'camera', 'camera_name', 
                  'snapshot', 'is_authorized', 'notes']

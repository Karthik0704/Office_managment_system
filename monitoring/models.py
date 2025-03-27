from django.db import models
from django.utils import timezone

class Camera(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    ip_address = models.GenericIPAddressField()
    port = models.IntegerField(default=8080)
    username = models.CharField(max_length=100, blank=True, null=True)
    password = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Maintenance')
    ], default='active')
    description = models.TextField(blank=True, null=True, default="")  # Made nullable with default
    stream_url = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.stream_url:
            if self.username and self.password:
                self.stream_url = f"rtsp://{self.username}:{self.password}@{self.ip_address}:{self.port}/stream"
            else:
                self.stream_url = f"rtsp://{self.ip_address}:{self.port}/stream"
        super().save(*args, **kwargs)

class MotionEvent(models.Model):
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name='motion_events')
    timestamp = models.DateTimeField(default=timezone.now)
    confidence = models.FloatField(default=0.0)
    snapshot = models.ImageField(upload_to='motion_events/', blank=True, null=True)
    
    def __str__(self):
        return f"Motion on {self.camera.name} at {self.timestamp}"

class PersonDetection(models.Model):
    motion_event = models.ForeignKey(MotionEvent, on_delete=models.CASCADE, related_name='person_detections')
    timestamp = models.DateTimeField(default=timezone.now)
    confidence = models.FloatField(default=0.0)  # Added default
    bounding_box = models.JSONField(null=True, default=dict)  # Made nullable with default
    snapshot = models.ImageField(upload_to='person_detections/', blank=True, null=True)
    
    def __str__(self):
        return f"Person detected at {self.timestamp}"

class MonitoringZone(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True, default="")  # Made nullable with default
    cameras = models.ManyToManyField(Camera, related_name='zones')
    coordinates = models.JSONField(null=True, default=list)  # Made nullable with default
    active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class ZoneActivity(models.Model):
    zone = models.ForeignKey(MonitoringZone, on_delete=models.CASCADE, related_name='activities')
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    person_count = models.IntegerField(default=0)
    snapshot = models.ImageField(upload_to='zone_activities/', blank=True, null=True)
    
    def __str__(self):
        return f"Activity in {self.zone.name} at {self.timestamp}"

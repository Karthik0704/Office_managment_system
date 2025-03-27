from django.contrib import admin
from .models import Camera, MotionEvent, PersonDetection, MonitoringZone, ZoneActivity

@admin.register(Camera)
class CameraAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'ip_address', 'status', 'created_at')
    list_filter = ('status', 'location')
    search_fields = ('name', 'location', 'ip_address')

@admin.register(MotionEvent)
class MotionEventAdmin(admin.ModelAdmin):
    list_display = ('camera', 'timestamp', 'confidence')
    list_filter = ('camera',)
    search_fields = ('camera__name',)
    date_hierarchy = 'timestamp'

@admin.register(PersonDetection)
class PersonDetectionAdmin(admin.ModelAdmin):
    list_display = ('motion_event', 'timestamp', 'confidence')
    list_filter = ('timestamp',)
    search_fields = ('motion_event__camera__name',)
    date_hierarchy = 'timestamp'

@admin.register(MonitoringZone)
class MonitoringZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'active')
    list_filter = ('active',)
    search_fields = ('name', 'description')
    filter_horizontal = ('cameras',)

@admin.register(ZoneActivity)
class ZoneActivityAdmin(admin.ModelAdmin):
    list_display = ('zone', 'camera', 'timestamp', 'person_count')
    list_filter = ('zone', 'camera')
    search_fields = ('zone__name', 'camera__name')
    date_hierarchy = 'timestamp'

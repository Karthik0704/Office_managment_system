from rest_framework import serializers
from .models import Department, Position, Employee, Attendance

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class PositionSerializer(serializers.ModelSerializer):
    department_name = serializers.ReadOnlyField(source='department.name')
    
    class Meta:
        model = Position
        fields = ['id', 'title', 'department', 'department_name', 'description', 'created_at', 'updated_at']

class EmployeeSerializer(serializers.ModelSerializer):
    department_name = serializers.ReadOnlyField(source='department.name')
    position_title = serializers.ReadOnlyField(source='position.title')
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Employee
        fields = ['id', 'user', 'employee_id', 'department', 'department_name', 
                  'position', 'position_title', 'full_name', 'date_of_birth', 
                  'hire_date', 'address', 'emergency_contact', 'emergency_phone', 
                  'created_at', 'updated_at']
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()

class AttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.ReadOnlyField(source='employee.user.get_full_name')
    duration_hours = serializers.SerializerMethodField()
    
    class Meta:
        model = Attendance
        fields = ['id', 'employee', 'employee_name', 'date', 'check_in_time', 
                  'check_out_time', 'status', 'notes', 'duration_hours', 
                  'created_at', 'updated_at']
    
    def get_duration_hours(self, obj):
        if obj.duration:
            # Convert timedelta to hours
            return round(obj.duration.total_seconds() / 3600, 2)
        return None

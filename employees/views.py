from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from .models import Department, Position, Employee, Attendance
from .serializers import (
    DepartmentSerializer, PositionSerializer, 
    EmployeeSerializer, AttendanceSerializer
)

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']

class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department']
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'department__name', 'created_at']

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department', 'position']
    search_fields = ['employee_id', 'user__first_name', 'user__last_name', 'user__email']
    ordering_fields = ['employee_id', 'user__first_name', 'hire_date']
    
    @action(detail=True, methods=['get'])
    def attendances(self, request, pk=None):
        employee = self.get_object()
        attendances = Attendance.objects.filter(employee=employee)
        serializer = AttendanceSerializer(attendances, many=True)
        return Response(serializer.data)

class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['employee', 'date', 'status']
    search_fields = ['employee__user__first_name', 'employee__user__last_name', 'notes']
    ordering_fields = ['date', 'employee__user__first_name', 'status']
    
    @action(detail=False, methods=['post'])
    def check_in(self, request):
        employee_id = request.data.get('employee_id')
        try:
            employee = Employee.objects.get(id=employee_id)
            today = timezone.now().date()
            
            # Check if attendance record exists for today
            attendance, created = Attendance.objects.get_or_create(
                employee=employee,
                date=today,
                defaults={'check_in_time': timezone.now(), 'status': 'present'}
            )
            
            if not created and not attendance.check_in_time:
                attendance.check_in_time = timezone.now()
                attendance.status = 'present'
                attendance.save()
                
            serializer = AttendanceSerializer(attendance)
            return Response(serializer.data)
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found"}, status=404)
    
    @action(detail=False, methods=['post'])
    def check_out(self, request):
        employee_id = request.data.get('employee_id')
        try:
            employee = Employee.objects.get(id=employee_id)
            today = timezone.now().date()
            
            try:
                attendance = Attendance.objects.get(employee=employee, date=today)
                attendance.check_out_time = timezone.now()
                attendance.save()
                serializer = AttendanceSerializer(attendance)
                return Response(serializer.data)
            except Attendance.DoesNotExist:
                return Response({"error": "No check-in record found for today"}, status=400)
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found"}, status=404)

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

def home_view(request):
    return HttpResponse("""
    <h1>Smart Office Management System</h1>
    <p>Welcome to the API server.</p>
    <ul>
        <li><a href="/admin/">Admin Interface</a></li>
        <li><a href="/api/auth/login/">API Login</a></li>
        <li><a href="/api/employees/departments/">Departments API</a></li>
        <li><a href="/api/monitoring/cameras/">Cameras API</a></li>
    </ul>
    """)

urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),
    path('api/employees/', include('employees.urls')),
    path('api/monitoring/', include('monitoring.urls')),  # Add this line
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

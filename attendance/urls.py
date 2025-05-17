from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('student-profile/', views.student_profile, name='student-profile'),
    path('teacher-profile/', views.teacher_profile, name='teacher-profile'),
    path('face-registration/', views.face_registration, name='face-registration'),
    path('mark-attendance/', views.mark_attendance, name='mark-attendance'),
    path('attendance-list/', views.AttendanceListView.as_view(), name='attendance-list'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('view-profile/', views.view_profile, name='view-profile'),
    path('attendance-summary/', views.attendance_summary, name='attendance-summary'),
] 
from django.urls import path
from . import views
app_name = "teacher_dashboard"
urlpatterns = [
    path('', views.teacher_dashboard ,name='teacher_dashboard'),
    path('teacher_profile/', views.teacher_profile, name='profile'),
    #path('take_attendance/<int:schedule_id>/', views.take_attendance, name='take_attendance'),
    path('leave_request/', views.leave_request, name='leave_request'),

    # ---- added ----
path('sections/', views.section_students, name='section_students'),
    path('sections/<int:section_id>/students/', views.students, name='students'),
    path("attendance-history/",views.attendance_history,name="attendance_history"),
    path('scan/', views.scan, name='scan'),
    path("reports/", views.attendance_reports, name="reports"),
    #path('teacher/attendance/<int:schedule_id>/',views.teacher_attendance,name='teacher_attendance'),
    path('attendance/manual/',views.manual_attendance,name='manual_attendance' ),
path('teacher/attendance/',views.teacher_attendance_list,name='teacher_attendance_list'),

]
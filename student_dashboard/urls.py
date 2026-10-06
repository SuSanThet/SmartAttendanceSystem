from django.urls import path

from admin_dashboard.urls import urlpatterns
from . import views
app_name = 'student_dashboard'
urlpatterns=[
    path('',views.student_dashboard_preview,name='student_dashboard'),
    path('profile/',views.student_profile,name='profile'),
    path('student_attendance/',views.my_attendance,name='my_attendance'),
    path('att_view/',views.attendance_statistics,name='attendance_statistics'),
    path('myqr/',views.myqr_view,name='myqr'),
    path('section/',views.student_timetable,name='mysection'),
    path("leave_request/",views.leave_request, name="leave_request"),
]
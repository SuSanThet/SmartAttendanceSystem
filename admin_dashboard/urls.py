from django.urls import path
from . import views
app_name = "admin_dashboard"
urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('student/', views.student, name='student'),
path('attendance/',views.att_rec,name='attendance'),
    path('sections/',views.section,name='sections'),

    path('QR/',views.myqr,name='QR'),

    path('profile/',views.profile,name='profile'),
    path('report/',views.report,name='report'),
    path("leave_requests/",views.admin_leave_requests,name="admin_leave_requests"),
    path('add_student/',views.add_student,name='add_student'),
    path('student_detail/<str:ID>/',views.student_detail,name='student_detail'),
    path('student_edit/<str:ID>/',views.student_edit,name='student_edit'),
    path('student_delete/<str:ID>/',views.student_delete,name='delete_student'),
    path('sections_details/<int:section_id>/',views.sections_details,name='sections_details'),
    path('student/<str:ID>/assign-section/',views.assign_student_section,name='assign_student_section'),




    path(
        'add-department/',
        views.add_department,
        name='add_department'
    ),

    path(
        'add-major/',
        views.add_major,
        name='add_major'
    ),

    path(
        'add-section/',
        views.add_section,
        name='add_section'
    ),

    path(
        'add-academic-class/',
        views.add_academic_class,
        name='add_academic_class'
    ),

    path(
        'add-teaching-assignment/',
        views.add_teaching_assignment,
        name='add_teaching'
    ),
path(
    'add-subject/',
    views.add_subject,
    name='add_subject'
),
]


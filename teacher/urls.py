from django.urls import path

from . import views

urlpatterns=[
path('teacher/',views.teacher,name='teacher'),
    path('add_teacher/',views.add_teacher,name='add_teacher'),
    path('teacher_detail/<str:TrID>/',views.teacher_detail,name='teacher_detail'),

path(
    "get-department-subjects/",
    views.get_department_subjects,
    name="get_department_subjects"
),
path(
    "teacher/edit/<str:TrID>/",
    views.edit_teacher,
    name="edit_teacher"
),
path(
    "teacher/delete/<str:TrID>/",
    views.teacher_delete,
    name="teacher_delete"
),
]
from django.urls import path
from . import views

urlpatterns = [
    path('schedule/builder/', views.schedule_builder, name='schedule_builder'),
    path('schedule/', views.schedule_list, name='schedule_list'),
    path('schedule/add/', views.schedule_add, name='schedule_add'),
    path('schedule/<int:pk>/edit/', views.schedule_edit, name='schedule_edit'),
    path('schedule/<int:pk>/delete/', views.schedule_delete, name='schedule_delete'),

    path('get-teachers-for-class/',
        views.get_teachers_for_class,name='get_teachers_for_class'),
]


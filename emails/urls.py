from django.urls import path

from . import views


app_name = "emails"


urlpatterns = [

    # Common entry
    path(
        "",
        views.email_home,
        name="email_home"
    ),

    # =========================
    # ADMIN
    # =========================

    path(
        "admin/",
        views.admin_email_home,
        name="admin_email_home"
    ),

    path(
        "admin/mail/<int:mail_id>/",
        views.admin_email_detail,
        name="admin_email_detail"
    ),

    path(
        "admin/send/",
        views.admin_send_email,
        name="admin_send_email"
    ),

    # =========================
    # TEACHER
    # =========================

    path(
        "teacher/",
        views.teacher_email_home,
        name="teacher_email_home"
    ),

    path(
        "teacher/mail/<int:mail_id>/",
        views.teacher_email_detail,
        name="teacher_email_detail"
    ),

    path(
        "teacher/send/",
        views.teacher_send_email,
        name="teacher_send_email"
    ),

    # =========================
    # STUDENT
    # =========================

    path(
        "student/",
        views.student_email_home,
        name="student_email_home"
    ),

    path(
        "student/mail/<int:mail_id>/",
        views.student_email_detail,
        name="student_email_detail"
    ),

    path(
        "student/send/",
        views.student_send_email,
        name="student_send_email"
    ),
# ADMIN

path(
    "admin/mail/<int:mail_id>/delete/",
    views.admin_delete_email,
    name="admin_delete_email"
),

# TEACHER

path(
    "teacher/mail/<int:mail_id>/delete/",
    views.teacher_delete_email,
    name="teacher_delete_email"
),

# STUDENT

path(
    "student/mail/<int:mail_id>/delete/",
    views.student_delete_email,
    name="student_delete_email"
),
    #Reply
path(
    "mail/<int:mail_id>/reply/",
    views.reply_email,
    name="reply_email"
),
]
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from admin_dashboard.models import EmailMessage


def get_mail_users(current_user):
    return User.objects.exclude(
        id=current_user.id
    ).exclude(
        email=""
    ).exclude(
        email__isnull=True
    ).order_by("email")


def get_inbox(user):
    return EmailMessage.objects.filter(
        receiver=user,
        is_deleted_by_receiver=False
    ).select_related(
        "sender",
        "receiver"
    ).order_by("-created_at")


def get_sent(user):
    return EmailMessage.objects.filter(
        sender=user,
        is_deleted_by_sender=False
    ).select_related(
        "sender",
        "receiver"
    ).order_by("-created_at")


def get_trash(user):
    return EmailMessage.objects.filter(
        Q(
            receiver=user,
            is_deleted_by_receiver=True
        ) |
        Q(
            sender=user,
            is_deleted_by_sender=True
        )
    ).select_related(
        "sender",
        "receiver"
    ).order_by("-created_at")


# =========================
# ADMIN
# =========================

@login_required
def admin_email_home(request):


    if request.user.role != "ADMIN":
        return redirect("emails:email_home")

    search = request.GET.get("search", "").strip()

    inbox = get_inbox(request.user)
    sent = get_sent(request.user)

    if search:
        inbox = inbox.filter(
            Q(sender__username__icontains=search) |
            Q(sender__email__icontains=search) |
            Q(subject__icontains=search) |
            Q(message__icontains=search)
        )

        sent = sent.filter(
            Q(receiver__username__icontains=search) |
            Q(receiver__email__icontains=search) |
            Q(subject__icontains=search) |
            Q(message__icontains=search)
        )
    trash = get_trash(request.user)
    users = get_mail_users(request.user)

    return render(
        request,
        "emails/admin_email.html",
        {
            "inbox": inbox,
            "sent": sent,
            "trash":trash,
            "users": users,
            "search": search,
        }
    )


@login_required
def admin_email_detail(request, mail_id):


    if request.user.role != "ADMIN":
        return redirect("emails:email_home")

    mail = get_object_or_404(
        EmailMessage.objects.select_related(
            "sender",
            "receiver"
        ),
        id=mail_id
    )

    if (
        mail.sender != request.user
        and mail.receiver != request.user
    ):
        messages.error(
            request,
            "You cannot view this email."
        )
        return redirect("emails:admin_email_home")

    if mail.receiver == request.user:
        mail.is_read = True
        mail.save(update_fields=["is_read"])

    return render(
        request,
        "emails/admin_email_detail.html",
        {
            "mail": mail,
        }
    )


@login_required
def admin_send_email(request):

    if request.user.role != "ADMIN":
        return redirect("emails:email_home")

    if request.method == "POST":

        receiver_id = request.POST.get("receiver")
        subject = request.POST.get("subject", "").strip()
        message = request.POST.get("message", "").strip()

        receiver = get_object_or_404(
            User,
            id=receiver_id
        )

        if receiver == request.user:
            messages.error(
                request,
                "You cannot send an email to yourself."
            )
            return redirect("emails:admin_email_home")

        if not receiver.email:
            messages.error(
                request,
                "This user does not have an email address."
            )
            return redirect("emails:admin_email_home")

        if not subject or not message:
            messages.error(
                request,
                "Subject and message are required."
            )
            return redirect("emails:admin_email_home")

        EmailMessage.objects.create(
            sender=request.user,
            receiver=receiver,
            subject=subject,
            message=message
        )


        messages.success(
            request,
            "Email sent successfully."
        )

    return redirect("emails:admin_email_home")

@login_required
def admin_delete_email(request, mail_id):

    if request.user.role != "ADMIN":
        return redirect("emails:email")

    mail = get_object_or_404(
        EmailMessage,
        id=mail_id
    )

    if mail.sender == request.user:
        mail.is_deleted_by_sender = True

    elif mail.receiver == request.user:
        mail.is_deleted_by_receiver = True

    else:
        messages.error(
            request,
            "You cannot delete this email."
        )
        return redirect("emails:admin_email_home")

    mail.save()
    messages.success(request, "Email moved to Trash.")
    return redirect("emails:admin_email_home")
# =========================
# TEACHER
# =========================

@login_required
def teacher_email_home(request):

    if request.user.role != "TEACHER":
        return redirect("emails:email_home")

    search = request.GET.get("search", "").strip()

    inbox = get_inbox(request.user)
    sent = get_sent(request.user)

    if search:
        inbox = inbox.filter(
            Q(sender__username__icontains=search) |
            Q(sender__email__icontains=search) |
            Q(subject__icontains=search) |
            Q(message__icontains=search)
        )

        sent = sent.filter(
            Q(receiver__username__icontains=search) |
            Q(receiver__email__icontains=search) |
            Q(subject__icontains=search) |
            Q(message__icontains=search)
        )

    users = get_mail_users(request.user)
    trash = get_trash(request.user)
    return render(
        request,
        "emails/teacher_email.html",
        {
            "inbox": inbox,
            "sent": sent,
            "trash": trash,
            "users": users,
            "search": search,
        }
    )


@login_required
def teacher_email_detail(request, mail_id):

    if request.user.role != "TEACHER":
        return redirect("emails:email_home")

    mail = get_object_or_404(
        EmailMessage.objects.select_related(
            "sender",
            "receiver"
        ),
        id=mail_id
    )

    if (
        mail.sender != request.user
        and mail.receiver != request.user
    ):
        messages.error(
            request,
            "You cannot view this email."
        )
        return redirect("emails:teacher_email_home")

    if mail.receiver == request.user:
        mail.is_read = True
        mail.save(update_fields=["is_read"])

    return render(
        request,
        "emails/teacher_email_detail.html",
        {
            "mail": mail,
        }
    )


@login_required
def teacher_send_email(request):

    if request.user.role != "TEACHER":
        return redirect("emails:email_home")

    if request.method == "POST":

        receiver_id = request.POST.get("receiver")
        subject = request.POST.get("subject", "").strip()
        message = request.POST.get("message", "").strip()

        receiver = get_object_or_404(
            User,
            id=receiver_id
        )

        if receiver == request.user:
            messages.error(
                request,
                "You cannot send an email to yourself."
            )
            return redirect("emails:teacher_email_home")

        if not receiver.email:
            messages.error(
                request,
                "This user does not have an email address."
            )
            return redirect("emails:teacher_email_home")

        if not subject or not message:
            messages.error(
                request,
                "Subject and message are required."
            )
            return redirect("emails:teacher_email_home")

        EmailMessage.objects.create(
            sender=request.user,
            receiver=receiver,
            subject=subject,
            message=message
        )
        messages.success(
            request,
            "Email sent successfully."
        )


    return redirect("emails:teacher_email_home")

@login_required
def teacher_delete_email(request, mail_id):

    if request.user.role != "TEACHER":
        return redirect("emails:email_home")

    mail = get_object_or_404(
        EmailMessage,
        id=mail_id
    )

    if mail.sender == request.user:
        mail.is_deleted_by_sender = True

    elif mail.receiver == request.user:
        mail.is_deleted_by_receiver = True

    else:
        messages.error(request, "You cannot delete this email.")
        return redirect("emails:teacher_email_home")

    mail.save()

    messages.success(request, "Email moved to Trash.")

    return redirect("emails:teacher_email_home")
# =========================
# STUDENT
# =========================

@login_required
def student_email_home(request):

    if request.user.role != "STUDENT":
        return redirect("emails:email_home")

    search = request.GET.get("search", "").strip()

    inbox = get_inbox(request.user)
    sent = get_sent(request.user)

    if search:
        inbox = inbox.filter(
            Q(sender__username__icontains=search) |
            Q(sender__email__icontains=search) |
            Q(subject__icontains=search) |
            Q(message__icontains=search)
        )

        sent = sent.filter(
            Q(receiver__username__icontains=search) |
            Q(receiver__email__icontains=search) |
            Q(subject__icontains=search) |
            Q(message__icontains=search)
        )

    users = get_mail_users(request.user)
    trash = get_trash(request.user)
    return render(
        request,
        "emails/student_email.html",
        {
            "inbox": inbox,
            "sent": sent,
            "trash": trash,
            "users": users,
            "search": search,
        }
    )


@login_required
def student_email_detail(request, mail_id):

    if request.user.role != "STUDENT":
        return redirect("emails:email_home")

    mail = get_object_or_404(
        EmailMessage.objects.select_related(
            "sender",
            "receiver"
        ),
        id=mail_id
    )

    if (
        mail.sender != request.user
        and mail.receiver != request.user
    ):
        messages.error(
            request,
            "You cannot view this email."
        )
        return redirect("emails:student_email_home")

    if mail.receiver == request.user:
        mail.is_read = True
        mail.save(update_fields=["is_read"])

    return render(
        request,
        "emails/student_email_detail.html",
        {
            "mail": mail,
        }
    )


@login_required
def student_send_email(request):

    if request.user.role != "STUDENT":
        return redirect("emails:email_home")

    if request.method == "POST":

        receiver_id = request.POST.get("receiver")
        subject = request.POST.get("subject", "").strip()
        message = request.POST.get("message", "").strip()

        receiver = get_object_or_404(
            User,
            id=receiver_id
        )

        if receiver == request.user:
            messages.error(
                request,
                "You cannot send an email to yourself."
            )
            return redirect("emails:student_email_home")

        if not receiver.email:
            messages.error(
                request,
                "This user does not have an email address."
            )
            return redirect("emails:student_email_home")

        if not subject or not message:
            messages.error(
                request,
                "Subject and message are required."
            )
            return redirect("emails:student_email_home")

        EmailMessage.objects.create(
            sender=request.user,
            receiver=receiver,
            subject=subject,
            message=message
        )

        messages.success(
            request,
            "Email sent successfully."
        )

    return redirect("emails:student_email_home")
@login_required
def student_delete_email(request, mail_id):

    if request.user.role != "STUDENT":
        return redirect("emails:email_home")

    mail = get_object_or_404(
        EmailMessage,
        id=mail_id
    )

    if mail.sender == request.user:
        mail.is_deleted_by_sender = True

    elif mail.receiver == request.user:
        mail.is_deleted_by_receiver = True

    else:
        messages.error(request, "You cannot delete this email.")
        return redirect("emails:student_email_home")

    mail.save()

    messages.success(request, "Email moved to Trash.")

    return redirect("emails:student_email_home")

# =========================
# COMMON ENTRY
# =========================

@login_required
def email_home(request):

    if request.user.role == "ADMIN":
        return redirect("emails:admin_email_home")

    elif request.user.role == "TEACHER":
        return redirect("emails:teacher_email_home")

    elif request.user.role == "STUDENT":
        return redirect("emails:student_email_home")

    return redirect("accounts:login")

def redirect_by_role(user, mail_id=None):

    if user.role == "ADMIN":

        if mail_id:
            return redirect(
                "emails:admin_email_detail",
                mail_id=mail_id
            )

        return redirect("emails:admin_email_home")

    elif user.role == "TEACHER":

        if mail_id:
            return redirect(
                "emails:teacher_email_detail",
                mail_id=mail_id
            )

        return redirect("emails:teacher_email_home")

    elif user.role == "STUDENT":

        if mail_id:
            return redirect(
                "emails:student_email_detail",
                mail_id=mail_id
            )

        return redirect("emails:student_email_home")

    return redirect("accounts:login")


def reply_email(request, mail_id):

    if not request.user.is_authenticated:
        return redirect("accounts:login")

    mail = get_object_or_404(
        EmailMessage,
        id=mail_id
    )

    if (
        mail.sender != request.user
        and mail.receiver != request.user
    ):
        messages.error(
            request,
            "You cannot reply to this email."
        )
        return redirect_by_role(request.user)

    if request.method == "POST":

        message = request.POST.get("message", "").strip()

        if not message:
            messages.error(
                request,
                "Reply message cannot be empty."
            )
            return redirect_by_role(
                request.user,
                mail.id
            )

        receiver = (
            mail.sender
            if mail.receiver == request.user
            else mail.receiver
        )

        subject = mail.subject

        if not subject.startswith("Re:"):
            subject = f"Re: {subject}"

        EmailMessage.objects.create(
            sender=request.user,
            receiver=receiver,
            subject=subject,
            message=message,
            parent=mail
        )

        messages.success(
            request,
            "Reply sent successfully."
        )

        return redirect_by_role(
            request.user,
            mail.id
        )

    return redirect_by_role(
        request.user,
        mail.id
    )
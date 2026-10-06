from django.shortcuts import render, redirect
from django.contrib.auth import login,logout
from .models import User
from django.contrib.auth.decorators import login_required

def login_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")
        selected_role = request.POST.get("role")

        users = User.objects.filter(
            username=username,
            role=selected_role
        )

        user = None

        for account in users:
            if account.check_password(password):
                user = account
                break

        if user is not None:

            login(request, user)

            if user.role == User.Role.ADMIN:
                return redirect("admin_dashboard:admin_dashboard")

            elif user.role == User.Role.TEACHER:
                return redirect("teacher_dashboard:teacher_dashboard")

            elif user.role == User.Role.STUDENT:
                return redirect("student_dashboard:student_dashboard")

        return render(
            request,
            "login.html",
            {"error": "Invalid username, password or role!"}
        )

    return render(request, "login.html")

from django.shortcuts import render, redirect
from django.contrib.auth import logout
@login_required
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('accounts:login')
    # If someone manually navigates via GET, redirect them to login or home
    return redirect('accounts:login')

from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect


@login_required
def change_password(request):

    if request.method == 'POST':

        form = PasswordChangeForm(
            request.user,
            request.POST
        )

        if form.is_valid():

            user = form.save()

            update_session_auth_hash(
                request,
                user
            )

            if user.role == 'ADMIN':
                return redirect('admin_dashboard:profile')

            elif user.role == 'TEACHER':
                return redirect('teacher_dashboard:profile')

            elif user.role == 'STUDENT':
                return redirect('student_dashboard:profile')

            return redirect('/')

    else:

        form = PasswordChangeForm(
            request.user
        )

    return render(
        request,
        'change_password.html',
        {
            'form': form
        }
    )
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.shortcuts import render, redirect

from admin_dashboard.models import Student


def forgot_password(request):

    if request.method == "POST":

        student_id = request.POST.get("student_id")
        phone = request.POST.get("phone")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        try:
            student = Student.objects.get(
                ID=student_id,
                phone=phone
            )
        except Student.DoesNotExist:
            messages.error(
                request,
                "Student ID or phone number is incorrect."
            )
            return render(
                request,
                "accounts/forgot_password.html"
            )

        if new_password != confirm_password:
            messages.error(
                request,
                "Passwords do not match."
            )
            return render(
                request,
                "accounts/forgot_password.html"
            )

        if len(new_password) < 8:
            messages.error(
                request,
                "Password must be at least 8 characters."
            )
            return render(
                request,
                "accounts/forgot_password.html"
            )

        student.user.set_password(new_password)
        student.user.save()

        messages.success(
            request,
            "Password reset successfully. You can now login."
        )

        return redirect("accounts:login")

    return render(
        request,
        "accounts/forgot_password.html"
    )
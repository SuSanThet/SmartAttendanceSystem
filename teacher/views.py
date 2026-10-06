from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404

from admin_dashboard.models import Teacher
from django.db.models import Q
from .forms import TeacherForm
from django.contrib.auth.decorators import login_required
from accounts.models import User
from timetable.models import Schedule
# Create your views here.

@login_required()

def teacher(request):

    tr = Teacher.objects.all()

    q = request.GET.get('q', '').strip()
    subject_id = request.GET.get('subject', '').strip()
    department_id = request.GET.get('department', '').strip()


    # Search by TrID
    if q:
        tr = tr.filter(
            TrID__icontains=q
        )


    # Subject filter
    if subject_id and subject_id != 'All Subjects':

        tr = tr.filter(
            subj__id=subject_id
        )


    # Department filter
    if department_id and department_id != 'All Departments':

        tr = tr.filter(
            dept_id=department_id
        )


    # Subjects assigned to each teacher
    for t in tr:

        t.teacher_subjects = t.subj.all()


    context = {

        'trs': tr,

        'subjects': Subject.objects.all(),

        'departments': Department.objects.all(),

        'selected_subject': subject_id,

        'selected_department': department_id,

        'search_query': q,

    }

    return render(
        request,
        'teacher/teacher.html',
        context
    )
from django.http import JsonResponse
from timetable.models import Subject, Department


def get_department_subjects(request):

    dept_id = request.GET.get("dept_id")

    subjects = Subject.objects.filter(
        department_id=dept_id
    ).order_by("code")

    data = [
        {
            "id": subject.id,
            "code": subject.code,
            "name": subject.name,
        }
        for subject in subjects
    ]

    return JsonResponse(data, safe=False)

def add_teacher(request):

    if request.method == 'POST':

        form = TeacherForm(request.POST)

        if form.is_valid():

            try:
                with transaction.atomic():

                    teacher = form.save(commit=False)

                    teacher.is_active = True

                    # Create User
                    user = User(
                        username=teacher.name,
                        role=User.Role.TEACHER,
                        account_id=teacher.TrID
                    )

                    user.set_password(teacher.TrID)
                    user.save()

                    # Connect Teacher with User
                    teacher.user = user
                    teacher.save()

                    # Save ManyToMany subjects
                    form.save_m2m()

                messages.success(
                    request,
                    'Teacher added successfully.'
                )

                return redirect('teacher')

            except Exception as e:

                messages.error(
                    request,
                    f'Failed to add teacher: {e}'
                )

    else:

        form = TeacherForm()

    return render(
        request,
        'teacher/add_teacher.html',
        {
            'form': form,
            'departments': Department.objects.all()
        }
    )
def teacher_detail(request, TrID):

    teacher = get_object_or_404(
        Teacher,
        TrID=TrID
    )

    schedules = (
        Schedule.objects
        .filter(teacher=teacher)
        .select_related(
            "subject",
            "class_group",
            "class_group__section"
        )
        .order_by(
            "class_group__section__sem",
            "class_group__section__name",
            "subject__code"
        )
    )

    teaching = {}

    for schedule in schedules:

        sem = schedule.class_group.section.sem
        section = schedule.class_group.section.name
        subject = schedule.subject

        if sem not in teaching:
            teaching[sem] = {}

        if subject.id not in teaching[sem]:
            teaching[sem][subject.id] = {
                "subject": subject,
                "sections": []
            }

        if section not in teaching[sem][subject.id]["sections"]:
            teaching[sem][subject.id]["sections"].append(section)

    return render(
        request,
        "teacher/teacher_detail.html",
        {
            "teacher": teacher,
            "teaching": teaching,
        }
    )
def edit_teacher(request, TrID):
    teacher = get_object_or_404(
        Teacher,
        TrID=TrID
    )

    if request.method == "POST":
        form = TeacherForm(
            request.POST,
            instance=teacher
        )

        if form.is_valid():
            with transaction.atomic():

                teacher = form.save()

                if teacher.user:
                    teacher.user.username = teacher.name
                    teacher.user.email = teacher.email
                    teacher.user.save()

            return redirect(
                "teacher_detail",
                TrID=teacher.TrID
            )

    else:
        form = TeacherForm(
            instance=teacher
        )

    return render(
        request,
        "teacher/edit_teacher.html",
        {
            "form": form,
            "teacher": teacher,
            "departments": Department.objects.all(),
        }
    )
def teacher_delete(request, TrID):

    if request.method == "POST":

        with transaction.atomic():

            teacher = get_object_or_404(
                Teacher,
                TrID=TrID
            )

            # Get User before deleting Teacher
            user = teacher.user

            # Delete Teacher
            teacher.delete()

            # Delete User
            if user:
                user.delete()

        messages.success(
            request,
            "Teacher has been deleted successfully."
        )

    return redirect("teacher")
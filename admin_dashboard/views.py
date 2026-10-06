from django.db import transaction,IntegrityError

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import render, redirect

from accounts.models import User
from timetable.utils import student_on_leave
from .forms import StudentForm, StudentSectionForm, SubjectForm
from django.db.models import Q
import calendar

from admin_dashboard.models import Student, Teacher, Section, TeachingAssignment, EmailMessage
from timetable.models import Attendance, Major, TimeSlot, Schedule, AcademicClass, Subject
from django.db.models import Count
from .forms import (
    DepartmentForm,
    MajorForm,
    SectionForm,
    AcademicClassForm,
    TeachingAssignmentForm,
)


def admin_dashboard(request):

    today = timezone.localdate()

    # students
    total_students = Student.objects.count()

    # teachers
    total_teachers = Teacher.objects.count()

    # sections
    total_sections = Section.objects.count()

    # TODAY'S ATTENDANCE


    today = timezone.localdate()

    day_map = {
        0: 'MON',
        1: 'TUE',
        2: 'WED',
        3: 'THU',
        4: 'FRI',
    }

    today_day = day_map.get(today.weekday())

    today_expected = 0
    today_present = 0
    today_percentage = 0

    if today_day:

        # Today's schedules
        today_schedules = Schedule.objects.filter(
            day=today_day
        ).select_related(
            'class_group',
            'class_group__section'
        )

        # Expected students
        for schedule in today_schedules:

            students = Student.objects.filter(
                section=schedule.class_group.section,
                is_active=True
            )

            for student in students:

                # Approved leave students
                # are excluded from today's expected count
                on_leave = LeaveRequest.objects.filter(
                    requester=student.user,
                    status='APPROVED',
                    start_date__lte=today,
                    end_date__gte=today
                ).exists()

                if not on_leave:
                    today_expected += 1

        # Present students for today's scheduled classes
        today_present = Attendance.objects.filter(
            date=today,
            status='PRESENT'
        ).count()

        # Calculate percentage
        if today_expected > 0:

            today_percentage = round(
                (today_present / today_expected) * 100,
                1
            )

        else:

            today_percentage = 0
    # monthly attendance
    monthly_data = []

    students = Student.objects.select_related(
        'section',
        'user'
    )


    for month in range(1, 13):

        start_date = date(
            today.year,
            month,
            1
        )

        end_date = date(
            today.year,
            month,
            monthrange(
                today.year,
                month
            )[1]
        )


        # future month
        if start_date > today:

            monthly_data.append({

                'month': start_date.strftime('%b'),

                'expected': 0,

                'attended': 0,

                'percentage': 0,

            })

            continue


        # current month
        if month == today.month:

            end_date = today


        expected = 0
        attended = 0


        # calculate expected classes
        for student in students:

            if not student.section:
                continue


            schedules = Schedule.objects.filter(
                class_group__section=student.section
            )


            student_expected = 0


            # scheduled classes
            for schedule in schedules:

                student_expected += count_schedule_occurrences(
                    schedule,
                    start_date,
                    end_date
                )


            # approved leave
            leaves = LeaveRequest.objects.filter(
                requester=student.user,
                status='APPROVED',
                start_date__lte=end_date,
                end_date__gte=start_date
            )


            leave_classes = 0


            for leave in leaves:

                leave_start = max(
                    leave.start_date,
                    start_date
                )

                leave_end = min(
                    leave.end_date,
                    end_date
                )


                for schedule in schedules:

                    leave_classes += count_schedule_occurrences(
                        schedule,
                        leave_start,
                        leave_end
                    )


            # remove leave classes
            student_expected = max(
                student_expected - leave_classes,
                0
            )


            expected += student_expected


            # student's attendance
            student_attended = Attendance.objects.filter(
                student=student,
                date__range=[
                    start_date,
                    end_date
                ],
                status='PRESENT'
            ).count()


            attended += student_attended


        # percentage
        if expected > 0:

            percentage = round(
                (attended / expected) * 100,
                1
            )

        else:

            percentage = 0


        monthly_data.append({

            'month': start_date.strftime('%b'),

            'expected': expected,

            'attended': attended,

            'percentage': percentage,

        })


    # recent leave requests
    recent_leaves = LeaveRequest.objects.select_related(
        'requester'
    ).order_by(
        '-created_at'
    )[:2]


    # recent emails
    recent_emails = EmailMessage.objects.select_related(
        'sender',
        'receiver'
    ).order_by(
        '-created_at'
    )[:2]


    # activities
    activities = []


    for leave in recent_leaves:

        activities.append({

            'type': 'leave',

            'object': leave,

            'created_at': leave.created_at,

        })


    for email in recent_emails:

        activities.append({

            'type': 'email',

            'object': email,

            'created_at': email.created_at,

        })


    # newest first
    activities.sort(
        key=lambda x: x['created_at'],
        reverse=True
    )


    # latest 5
    activities = activities[:5]


    context = {

        'total_students': total_students,

        'total_teachers': total_teachers,

        'total_sections': total_sections,

        'today_percentage': today_percentage,

        'monthly_data': monthly_data,

        'activities': activities,

    }


    return render(
        request,
        'admin_dashboard/dashboard.html',
        context
    )
def student(request):

    students = Student.objects.select_related("section").all()

    q = request.GET.get("q")
    sem = request.GET.get("semester")
    section = request.GET.get("section")

    if q:
        students = students.filter(
            Q(name__icontains=q) |
            Q(ID__icontains=q) |
            Q(email__icontains=q)
        )

    if sem and sem != "All":
        students = students.filter(
            section__sem=sem
        )

    if section and section != "All":
        students = students.filter(
            section__name=section
        )

    # DB ထဲက section အားလုံး
    sections = Section.objects.order_by("name")

    # DB ထဲက semester အားလုံး
    semesters = (
        Section.objects
        .values_list("sem", flat=True)
        .distinct()
        .order_by("sem")
    )

    return render(
        request,
        "admin_dashboard/student.html",
        {
            "students": students,
            "sections": sections,
            "semesters": semesters,
            "q": q,
            "selected_semester": sem,
            "selected_section": section,
        }
    )

from datetime import date, timedelta


def att_rec(request):

    current_year = date.today().year

    sections = Section.objects.all().order_by(
        'sem',
        'name'
    )

    selected_section = request.GET.get('section')
    selected_date = request.GET.get('date')

    # current date
    if selected_date:
        selected_date = date.fromisoformat(selected_date)
    else:
        selected_date = date.today()

    # selected date ရဲ့ weekday
    day_map = {
        0: 'MON',
        1: 'TUE',
        2: 'WED',
        3: 'THU',
        4: 'FRI',
    }

    day_code = day_map.get(selected_date.weekday())

    records = []

    if day_code:

        schedules = Schedule.objects.filter(
            day=day_code
        ).select_related(
            'class_group',
            'class_group__section',
            'subject',
            'teacher',
            'time_slot',
        )

        # Section filter
        if selected_section:
            schedules = schedules.filter(
                class_group__section_id=selected_section
            )

        for schedule in schedules:

            section = schedule.class_group.section

            students = Student.objects.filter(
                section=section
            ).order_by('ID')

            for student in students:

                attendance = Attendance.objects.filter(
                    student=student,
                    schedule=schedule,
                    date=selected_date
                ).first()

                if attendance:

                    status = attendance.status
                    method = attendance.method
                    remark = attendance.remark

                else:

                    # No attendance record = Absent
                    status = 'ABSENT'
                    method = None
                    remark = 'No Attendance'

                records.append({
                    'student': student,
                    'schedule': schedule,
                    'section': section,
                    'attendance': attendance,
                    'status': status,
                    'method': method,
                    'remark': remark,
                })

    return render(
        request,
        'admin_dashboard/attendance.html',
        {
            'records': records,
            'sections': sections,
            'selected_section': selected_section,
            'selected_date': selected_date,
            'current_year': current_year,
        }
    )

def section(request):

    sections = Section.objects.annotate(
        student_count=Count("students")
    ).prefetch_related(
        "academic_class__major"
    )
    context = {

        'sections': sections,

        'academic_form': AcademicClassForm(),

        'teaching_form': TeachingAssignmentForm(),

        'section_form': SectionForm(),

        'major_form': MajorForm(),

        'department_form': DepartmentForm(),
        'subject_form': SubjectForm(),
    }

    return render(
        request,
        "admin_dashboard/section.html",
        context
    )

from django.shortcuts import render, get_object_or_404
from .models import Student

def myqr(request):

    student = None
    student_id = request.GET.get('ID')

    # Search လုပ်ထား/မထား သိဖို့
    searched = bool(student_id)

    if student_id:
        try:
            student = Student.objects.get(ID=student_id)
        except Student.DoesNotExist:
            student = None

    return render(
        request,
        'admin_dashboard/QR.html',
        {
            'student': student,
            'searched': searched,
        }
    )
def profile(request):
    return render(request,'admin_dashboard/profile.html')

from calendar import monthrange

def count_schedule_occurrences(schedule, start_date, end_date):

    day_map = {
        0: 'MON',
        1: 'TUE',
        2: 'WED',
        3: 'THU',
        4: 'FRI',
    }

    count = 0
    current = start_date

    while current <= end_date:

        if day_map.get(current.weekday()) == schedule.day:
            count += 1

        current += timedelta(days=1)

    return count

def count_valid_schedule_occurrences(
    schedule,
    start_date,
    end_date,
    student
):
    # count expected classes

    count = 0
    current_date = start_date

    while current_date <= end_date:

        # check schedule day

        selected_day = current_date.strftime('%a').upper()
        schedule_day = schedule.day.upper()

        if selected_day == schedule_day:

            # skip approved leave

            if student_on_leave(
                student,
                current_date
            ):
                current_date += timedelta(days=1)
                continue

            count += 1

        current_date += timedelta(days=1)

    return count


def report(request):

    # today

    today = timezone.localdate()

    # month year

    try:

        year = int(
            request.GET.get(
                'year',
                today.year
            )
        )

        month = int(
            request.GET.get(
                'month',
                today.month
            )
        )

    except (ValueError, TypeError):

        year = today.year
        month = today.month

    # date range

    start_date = date(
        year,
        month,
        1
    )

    end_date = date(
        year,
        month,
        monthrange(
            year,
            month
        )[1]
    )

    # current month

    if (
        year == today.year
        and
        month == today.month
    ):

        end_date = today

    # sections

    sections = Section.objects.all().order_by(
        'sem',
        'name'
    )

    # filters

    search = request.GET.get(
        'search',
        ''
    ).strip()

    section_id = request.GET.get(
        'section',
        ''
    )

    # students

    students = Student.objects.select_related(
        'user',
        'section'
    ).all().order_by(
        'ID'
    )

    # search

    if search:

        students = students.filter(
            Q(
                ID__icontains=search
            )
            |
            Q(
                name__icontains=search
            )
        )

    # section filter

    if section_id:

        students = students.filter(
            section_id=section_id
        )

    # schedules

    schedules = Schedule.objects.select_related(
        'class_group',
        'class_group__section',
        'subject',
        'time_slot'
    )

    # student reports

    student_reports = []

    for student in students:

        # no section

        if not student.section:

            student_reports.append({

                'student': student,
                'section': None,
                'expected': 0,
                'attended': 0,
                'present': 0,
                'late': 0,
                'absent': 0,
                'percentage': 0,

            })

            continue

        # student schedules

        student_schedules = schedules.filter(
            class_group__section=student.section
        )

        # expected

        expected = 0

        for schedule in student_schedules:

            expected += count_valid_schedule_occurrences(
                schedule,
                start_date,
                end_date,
                student
            )

        # attendance

        attendance_qs = Attendance.objects.filter(
            student=student,
            date__range=[
                start_date,
                end_date
            ]
        )

        # present

        present = attendance_qs.filter(
            status='PRESENT'
        ).count()

        # late

        late = attendance_qs.filter(
            status='LATE'
        ).count()

        # absent

        absent = attendance_qs.filter(
            status='ABSENT'
        ).count()

        # attended

        attended = present + late

        # percentage

        if expected > 0:

            percentage = round(
                (
                    attended / expected
                ) * 100,
                1
            )

        else:

            percentage = 0

        student_reports.append({

            'student': student,

            'section': student.section,

            'expected': expected,

            'attended': attended,

            'present': present,

            'late': late,

            'absent': absent,

            'percentage': percentage,

        })

    # below 75

    below_75 = [

        item

        for item in student_reports

        if (
            item['expected'] > 0
            and
            item['percentage'] < 75
        )

    ]

    # overall attendance

    total_expected = sum(

        item['expected']

        for item in student_reports

    )

    total_attended = sum(

        item['attended']

        for item in student_reports

    )

    if total_expected > 0:

        overall_attendance = round(
            (
                total_attended
                /
                total_expected
            ) * 100,
            1
        )

    else:

        overall_attendance = 0

    # section reports

    section_reports = []

    for section in sections:

        section_students = [

            item

            for item in student_reports

            if item['section'] == section

        ]

        section_expected = sum(

            item['expected']

            for item in section_students

        )

        section_attended = sum(

            item['attended']

            for item in section_students

        )

        section_present = sum(

            item['present']

            for item in section_students

        )

        section_late = sum(

            item['late']

            for item in section_students

        )

        section_absent = sum(

            item['absent']

            for item in section_students

        )

        # percentage

        if section_expected > 0:

            section_percentage = round(
                (
                    section_attended
                    /
                    section_expected
                ) * 100,
                1
            )

        else:

            section_percentage = 0

        # status

        if section_percentage >= 75:

            status = 'Good'

        elif section_percentage >= 60:

            status = 'Warning'

        else:

            status = 'Low'

        section_reports.append({

            'section': section,

            'students': len(
                section_students
            ),

            'expected': section_expected,

            'attended': section_attended,

            'present': section_present,

            'late': section_late,

            'absent': section_absent,

            'percentage': section_percentage,

            'status': status,

        })

    # context

    context = {

        'total_students':
            students.count(),

        'total_sections':
            sections.count(),

        'overall_attendance':
            overall_attendance,

        'below_75_count':
            len(below_75),

        'student_reports':
            student_reports,

        'below_75':
            below_75,

        'section_reports':
            section_reports,

        'sections':
            sections,

        'selected_month':
            month,

        'selected_year':
            year,

        'search':
            search,

        'selected_section':
            section_id,

        'start_date':
            start_date,

        'end_date':
            end_date,

    }

    return render(
        request,
        'admin_dashboard/report.html',
        context
    )
def sections_details(request, section_id):

    section = get_object_or_404(
        Section,
        id=section_id
    )

    academic_class = AcademicClass.objects.filter(
        section=section
    ).first()

    schedules = Schedule.objects.none()

    if academic_class:
        schedules = Schedule.objects.filter(
            class_group=academic_class
        ).select_related(
            'subject',
            'teacher',
            'time_slot'
        ).order_by(
            'time_slot__start_time'
        )

    assignments = TeachingAssignment.objects.filter(
        section=section
    ).select_related(
        'teacher'
    )
    for assignment in assignments:
        assignment.subjects = Subject.objects.filter(
            schedule__class_group=academic_class,
            schedule__teacher=assignment.teacher
        ).distinct()

    students = Student.objects.filter(
        section=section
    ).order_by(
        'ID'
    )

    time_slots = TimeSlot.objects.all().order_by(
        'start_time'
    )

    return render(
        request,
        'admin_dashboard/section_details.html',
        {
            'section': section,
            'academic_class': academic_class,
            'schedules': schedules,
            'assignments': assignments,
            'students': students,
            'time_slots': time_slots,
        }
    )

def add_student(request):

    sections = Section.objects.all().order_by("sem", "name")
    majors = Major.objects.all().order_by("name")

    if request.method == "POST":

        form = StudentForm(request.POST)

        print("POST DATA:", request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():

                    print("CLEANED SECTION:", form.cleaned_data.get("section"))
                    print("CLEANED SECTION ID:",
                          form.cleaned_data.get("section").id
                          if form.cleaned_data.get("section")
                          else None)

                    student = form.save(commit=False)

                    print("STUDENT SECTION:", student.section)
                    print("STUDENT SECTION ID:", student.section_id)

                    student.is_active = True

                    user = User(
                        username=student.name,
                        role=User.Role.STUDENT,
                        account_id=student.ID,
                        email=student.email,
                    )

                    user.set_password(student.ID)
                    user.save()

                    student.user = user
                    student.save()

                    print("AFTER SAVE SECTION:", student.section)
                    print("AFTER SAVE SECTION ID:", student.section_id)

                return redirect("admin_dashboard:student")

            except IntegrityError as e:
                print("ADD STUDENT ERROR:", repr(e))
                messages.error(request, "Student account already exists.")
        else:

            print("FORM ERRORS:", form.errors)

            messages.error(
                request,
                "Please correct the errors below."
            )

    else:
        form = StudentForm()

    return render(
        request,
        "admin_dashboard/add_student.html",
        {
            "form": form,
            "sections": sections,
            "majors": majors,
        }
    )
def student_detail(request,ID):
    student=Student.objects.get(ID=ID)
    return render(request,'admin_dashboard/student_detail.html',{'student':student})
def student_edit(request, ID):

    student = get_object_or_404(
        Student,
        ID=ID
    )

    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        section_id = request.POST.get("section")
        major_id = request.POST.get("major")

        with transaction.atomic():

            student.name = name
            student.email = email
            student.phone = phone
            student.section_id = section_id

            if major_id:
                student.major_id = major_id
            else:
                student.major = None

            student.save()

            if student.user:

                student.user.username = name
                student.user.email = email
                student.user.save()

        messages.success(
            request,
            "Student information updated successfully."
        )

        return redirect(
            "admin_dashboard:student_detail",
            ID=student.ID
        )

    sections = Section.objects.all().order_by(
        "sem",
        "name"
    )

    majors = Major.objects.all().order_by(
        "name"
    )

    return render(
        request,
        "admin_dashboard/student_edit.html",
        {
            "student": student,
            "sections": sections,
            "majors": majors,
        }
    )
def student_delete(request, ID):
    if request.method == "POST":
        with transaction.atomic():
            student = get_object_or_404(Student, ID=ID)

            user = student.user
            student.delete()

            if user:
                user.delete()

    return redirect("admin_dashboard:student")

def assign_student_section(request, ID):

    student = get_object_or_404(Student, ID=ID)

    if request.method == 'POST':
        form = StudentSectionForm(request.POST, instance=student)

        if form.is_valid():
            form.save()
            return redirect('student')

    else:
        form = StudentSectionForm(instance=student)

    return render(
        request,
        'admin_dashboard/assign_section.html',
        {
            'student': student,
            'form': form
        }
    )

from django.utils import timezone

from admin_dashboard.models import LeaveRequest
def update_expired_leaves():

    today = timezone.localdate()

    expired_leaves = LeaveRequest.objects.filter(
        status="APPROVED",
        end_date__lt=today
    ).select_related("requester")

    for leave in expired_leaves:

        user = leave.requester

        if hasattr(user, "student"):

            student = user.student

            if not student.is_active:
                student.is_active = True
                student.save(
                    update_fields=["is_active"]
                )

        elif hasattr(user, "teacher"):

            teacher = user.teacher

            if not teacher.is_active:
                teacher.is_active = True
                teacher.save(
                    update_fields=["is_active"]
                )

def admin_leave_requests(request):

    # leave ပြီးသွားရင် active ပြန်လုပ်
    update_expired_leaves()

    if request.method == "POST":

        approve_id = request.POST.get("action_approve")
        reject_id = request.POST.get("action_reject")

        if approve_id:

            leave = get_object_or_404(
                LeaveRequest,
                id=approve_id
            )

            # approve leave
            leave.status = "APPROVED"
            leave.reviewed_by = request.user
            leave.reviewed_at = timezone.now()
            leave.save()

            # inactive immediately
            user = leave.requester

            if hasattr(user, "student"):

                student = user.student
                student.is_active = False
                student.save(
                    update_fields=["is_active"]
                )

            elif hasattr(user, "teacher"):

                teacher = user.teacher
                teacher.is_active = False
                teacher.save(
                    update_fields=["is_active"]
                )

        elif reject_id:

            leave = get_object_or_404(
                LeaveRequest,
                id=reject_id
            )

            leave.status = "REJECTED"
            leave.reviewed_by = request.user
            leave.reviewed_at = timezone.now()
            leave.save()

        return redirect(request.path)

    leave_requests = LeaveRequest.objects.select_related(
        "requester",
        "reviewed_by"
    ).order_by("-created_at")

    return render(
        request,
        "admin_dashboard/leave_requests.html",
        {
            "leave_requests": leave_requests
        }
    )

def add_department(request):

    if request.method == 'POST':

        form = DepartmentForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Department added successfully.'
            )

            return redirect('admin_dashboard:sections')

    else:
        form = DepartmentForm()

    return render(
        request,
        'admin_dashboard/add_department.html',
        {'form': form}
    )


def add_major(request):

    if request.method == 'POST':

        form = MajorForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Major added successfully.'
            )

            return redirect('admin_dashboard:sections')

    else:
        form = MajorForm()

    return render(
        request,
        'admin_dashboard/add_major.html',
        {'form': form}
    )


def add_section(request):

    if request.method == 'POST':

        form = SectionForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Section added successfully.'
            )

            return redirect('admin_dashboard:sections')

    else:
        form = SectionForm()

    return render(
        request,
        'admin_dashboard/add_section.html',
        {'form': form}
    )


def add_academic_class(request):

    if request.method == 'POST':

        form = AcademicClassForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Academic class added successfully.'
            )

            return redirect('admin_dashboard:sections')

    else:
        form = AcademicClassForm()

    return render(
        request,
        'admin_dashboard/add_academic_class.html',
        {'form': form}
    )


def add_teaching_assignment(request):

    if request.method == 'POST':

        form = TeachingAssignmentForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Teaching assignment added successfully.'
            )

            return redirect('admin_dashboard:sections')

    else:
        form = TeachingAssignmentForm()

    return render(
        request,
        'admin_dashboard/add_teaching.html',
        {'form': form}
    )
def add_subject(request):

    if request.method == 'POST':

        form = SubjectForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Subject added successfully.'
            )

            return redirect('admin_dashboard:sections')

    else:
        form = SubjectForm()

    return render(
        request,
        'admin_dashboard/add_subject.html',
        {'form': form}
    )
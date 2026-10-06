from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
import calendar

from .models import TeacherProfile
from admin_dashboard.models import Teacher, TeachingAssignment, Student, Section, LeaveRequest, EmailMessage

# ---- added: needed for the Students page (pagination + safe query strings) ----

from datetime import date, timedelta, timezone, datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction

import json

from django.http import JsonResponse

from django.views.decorators.http import require_http_methods
from timetable.models import Subject
from datetime import date, timedelta

def teacher_dashboard(request):
    profile_obj = get_current_teacher_profile(request)
    try:
        teacher = request.user.teacher

    except Teacher.DoesNotExist:

        return render(
            request,
            'teacher_dashboard/dashboard.html',
            {
                'profile':profile_obj,
                'teachers': None,
                'total_students': 0,
                'present_today': 0,
                'absent_today': 0,
                'attendance_rate': 0,
                'monthly_attendance_rate': 0,
                'absent_percent': 0,
                'todays_classes': [],
                'notifications': [],
                'top_attendance': [],
                'monthly_labels': [],
                'monthly_data': [],
            }
        )

    today = date.today()


    # TEACHING ASSIGNMENTS


    assignments = TeachingAssignment.objects.filter(
        teacher=teacher
    )

    section_ids = assignments.values_list(
        'section_id',
        flat=True
    ).distinct()



    # ALL STUDENTS ASSIGNED TO THIS TEACHER


    teacher_students = Student.objects.filter(
        section_id__in=section_ids,
        is_active=True
    ).distinct()

    total_students = teacher_students.count()



    # SCHEDULES


    schedules = Schedule.objects.filter(
        teacher=teacher,
        class_group__section_id__in=section_ids
    ).select_related(
        'subject',
        'class_group',
        'class_group__section',
        'time_slot',
    )



    # MONTH


    month_start = today.replace(day=1)

    last_day = calendar.monthrange(
        today.year,
        today.month
    )[1]

    month_end = today.replace(day=last_day)

    # TODAY ATTENDANCE

    today_day = today.strftime('%a').upper()[:3]

    today_schedules = schedules.filter(
        day=today_day
    )

    today_schedule_ids = today_schedules.values_list(
        'id',
        flat=True
    ).distinct()


    # ONLY SECTIONS HAVING A TIMETABLE TODAY

    today_section_ids = today_schedules.values_list(
        'class_group__section_id',
        flat=True
    ).distinct()

    # ONLY STUDENTS FROM TODAY'S SECTIONS

    today_students = Student.objects.filter(
        section_id__in=today_section_ids,
        is_active=True
    ).distinct()

    total_students_today = today_students.count()

    # TODAY ATTENDANCE RECORDS

    today_attendance = Attendance.objects.filter(
        schedule_id__in=today_schedule_ids,
        student__in=today_students,
        date=today
    )

    # PRESENT


    present_today = today_attendance.filter(
        status='PRESENT'
    ).values(
        'student'
    ).distinct().count()

    # LATE

    late_today = today_attendance.filter(
        status='LATE'
    ).values(
        'student'
    ).distinct().count()

    # ATTENDED
    # PRESENT + LATE

    attended_today = today_attendance.filter(
        status__in=[
            'PRESENT',
            'LATE'
        ]
    ).values(
        'student'
    ).distinct().count()


    # ---------------------------------------------------------
    # ABSENT
    #
    # If a student has no attendance record today,
    # that student is considered absent.
    # ---------------------------------------------------------

    if total_students_today > 0:

        absent_today = max(
            total_students_today - attended_today,
            0
        )

    else:

        absent_today = 0


    # TODAY ATTENDANCE RATE

    if total_students_today > 0:

        attendance_rate = round(
            (attended_today / total_students_today) * 100,
            1
        )

        absent_percent = round(
            (absent_today / total_students_today) * 100,
            1
        )

    else:

        attendance_rate = 0
        absent_percent = 0



    # MONTHLY EXPECTED


    monthly_expected = 0

    for schedule in schedules:

        occurrences = count_schedule_occurrences(
            schedule,
            month_start,
            month_end
        )

        student_count = Student.objects.filter(
            section_id=schedule.class_group.section_id,
            is_active=True
        ).count()

        monthly_expected += (
            occurrences * student_count
        )



    # MONTHLY ATTENDANCE


    monthly_attendance = Attendance.objects.filter(
        schedule__teacher=teacher,
        schedule__class_group__section_id__in=section_ids,
        date__year=today.year,
        date__month=today.month
    )


    monthly_present = monthly_attendance.filter(
        status='PRESENT'
    ).count()


    monthly_late = monthly_attendance.filter(
        status='LATE'
    ).count()


    monthly_attended = (
        monthly_present +
        monthly_late
    )


    if monthly_expected > 0:

        monthly_attendance_rate = round(
            (monthly_attended / monthly_expected) * 100,
            1
        )

        monthly_attendance_rate = min(
            monthly_attendance_rate,
            100
        )

    else:

        monthly_attendance_rate = 0


    # TODAY'S CLASSES

    todays_classes = []

    now = datetime.now().time()

    for schedule in today_schedules:

        start_time = schedule.time_slot.start_time
        end_time = schedule.time_slot.end_time

        if now < start_time:

            status = 'Upcoming'

        elif start_time <= now < end_time:

            status = 'Ongoing'

        else:

            status = 'Completed'

        todays_classes.append({
            'time': str(schedule.time_slot),
            'code': schedule.subject.code,
            'name': str(schedule.class_group),
            'status': status,
        })



    # MONTHLY OVERVIEW


    monthly_labels = [
        'Jan',
        'Feb',
        'Mar',
        'Apr',
        'May',
        'Jun',
        'Jul',
        'Aug',
        'Sep',
        'Oct',
        'Nov',
        'Dec'
    ]

    monthly_data = []


    for month_number in range(1, 13):

        start_date = date(
            today.year,
            month_number,
            1
        )

        last_day = calendar.monthrange(
            today.year,
            month_number
        )[1]

        end_date = date(
            today.year,
            month_number,
            last_day
        )


        expected = 0


        for schedule in schedules:

            occurrences = count_schedule_occurrences(
                schedule,
                start_date,
                end_date
            )

            student_count = Student.objects.filter(
                section_id=schedule.class_group.section_id,
                is_active=True
            ).count()

            expected += (
                occurrences * student_count
            )


        attended = Attendance.objects.filter(
            schedule__teacher=teacher,
            schedule__class_group__section_id__in=section_ids,
            date__year=today.year,
            date__month=month_number,
            status__in=[
                'PRESENT',
                'LATE'
            ]
        ).count()


        if expected > 0:

            percentage = round(
                (attended / expected) * 100,
                1
            )

            percentage = min(
                percentage,
                100
            )

        else:

            percentage = 0


        monthly_data.append({
            'label': calendar.month_abbr[month_number],
            'percentage': percentage,
        })



    # TOP ATTENDANCE


    top_attendance = []


    for student in teacher_students:

        student_schedules = schedules.filter(
            class_group__section_id=student.section_id
        )


        expected = 0


        for schedule in student_schedules:

            expected += count_schedule_occurrences(
                schedule,
                month_start,
                month_end
            )


        attended = Attendance.objects.filter(
            student=student,
            schedule__teacher=teacher,
            schedule__class_group__section_id=student.section_id,
            date__year=today.year,
            date__month=today.month,
            status__in=[
                'PRESENT',
                'LATE'
            ]
        ).count()


        if expected > 0:

            percentage = round(
                (attended / expected) * 100,
                1
            )

            percentage = min(
                percentage,
                100
            )

        else:

            percentage = 0


        top_attendance.append({
            'name': student.name,
            'class_name': str(student.section),
            'attendance': percentage,
        })


    top_attendance.sort(
        key=lambda x: x['attendance'],
        reverse=True
    )

    top_attendance = top_attendance[:2]



    # NOTIFICATIONS


    email_messages = EmailMessage.objects.filter(
        receiver=teacher.user,
        is_deleted_by_receiver=False
    ).select_related(
        'sender'
    ).order_by(
        '-created_at'
    )


    notifications = []


    unread_notifications = EmailMessage.objects.filter(
        receiver=teacher.user,
        is_read=False,
        is_deleted_by_receiver=False
    ).count()


    for email in email_messages[:2]:

        notifications.append({
            'text': email.subject,
            'time': email.created_at,
            'sender': email.sender.username,
            'is_read': email.is_read,
        })



    context = {

        'teachers': teacher,

        'profile': profile_obj,

        'unread_notifications': unread_notifications,


        # All students assigned to teacher
        'total_students': total_students,


        # Today's timetable-based attendance
        'present_today': present_today,

        'absent_today': absent_today,

        'attendance_rate': attendance_rate,

        'absent_percent': absent_percent,


        # Monthly
        'monthly_attendance_rate': monthly_attendance_rate,


        # Today's classes
        'todays_classes': todays_classes,


        # Notifications
        'notifications': notifications,


        # Top attendance
        'top_attendance': top_attendance,


        # Monthly chart
        'monthly_labels': monthly_labels,

        'monthly_data': monthly_data,


        'current_year': today.year,
    }


    return render(
        request,
        'teacher_dashboard/dashboard.html',
        context
    )
# Helper function to get the current teacher profile
def get_current_teacher_profile(request):

    if not request.user.is_authenticated:
        return None

    teacher = Teacher.objects.filter(
        user=request.user
    ).first()

    if not teacher:
        return None

    profile_obj, _ = TeacherProfile.objects.get_or_create(
        teacher=teacher
    )

    return profile_obj
# 1. Teacher Profile View
def teacher_profile(request):
    profile_obj = get_current_teacher_profile(request)
    teacher=Teacher.objects.get(user=request.user)
    if request.method == 'POST':
        if 'profile_pic' in request.FILES:
            profile_obj.profile_pic = request.FILES['profile_pic']
            profile_obj.save()
            return redirect(request.path)

        if 'delete_pic' in request.POST:
            if profile_obj.profile_pic:
                profile_obj.profile_pic.delete(save=True)
            return redirect(request.path)

    return render(request, 'teacher_dashboard/profileteacher.html', {'profile': profile_obj,'teacher': teacher})

# 2. Take Attendance View

# 3. Leave Request View
from datetime import date
from django.utils import timezone
from django.contrib import messages


def leave_request(request):
    profile_obj = get_current_teacher_profile(request)

    teacher = profile_obj.teacher
    if request.method == "POST":

        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        reason = request.POST.get("reason", "").strip()

        if not start_date or not end_date:
            messages.error(
                request,
                "Please select From Date and To Date."
            )
            return redirect(request.path)

        start_date = date.fromisoformat(start_date)
        end_date = date.fromisoformat(end_date)

        today = timezone.localdate()

        if start_date < today:
            messages.error(
                request,
                "From date cannot be before today."
            )
            return redirect(request.path)

        if end_date < today:
            messages.error(
                request,
                "To date cannot be before today."
            )
            return redirect(request.path)

        if end_date < start_date:
            messages.error(
                request,
                "To date cannot be before From date."
            )
            return redirect(request.path)

        LeaveRequest.objects.create(
            requester=request.user,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            status="PENDING"
        )

        messages.success(
            request,
            "Leave request submitted successfully."
        )

        return redirect(request.path)

    leave_requests = LeaveRequest.objects.filter(
        requester=request.user
    ).order_by("-created_at")

    return render(
        request,
        "teacher_dashboard/leave_request.html",
        {
            'profile': profile_obj,
            "leave_requests": leave_requests,
        }
    )



def get_page_range(current, total):
    """Build a compact page list like [1, 2, 3, '...', 42] for the pager."""
    if total <= 7:
        return list(range(1, total + 1))

    pages = {1, 2, 3, total, current - 1, current, current + 1}
    pages = sorted(p for p in pages if 1 <= p <= total)

    result = []
    previous = None
    for p in pages:
        if previous is not None and p - previous > 1:
            result.append('...')
        result.append(p)
        previous = p
    return result
@login_required
@require_http_methods(["GET", "POST"])
def scan(request):

    # GET → QR Scanner Page
    profile_obj = get_current_teacher_profile(request)

    if request.method == "GET":
        return render(
            request,
            "teacher_dashboard/scan.html",{'profile': profile_obj}
        )

    # Read QR Data

    try:
        data = json.loads(request.body)
        student_id = data.get("student_id")

    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "message": "Invalid QR data."
        })


    if not student_id:
        return JsonResponse({
            "success": False,
            "message": "Student ID not found."
        })


    # Find Student


    student = Student.objects.filter(
        ID=student_id,
        is_active=True
    ).select_related(
        "section"
    ).first()


    if not student:
        return JsonResponse({
            "success": False,
            "message": "Student not found."
        })

    # Current Teacher

    teacher = get_object_or_404(
        Teacher,
        user=request.user
    )

    # Current Date & Time


    now = timezone.localtime()

    today = now.date()
    current_time = now.time()


    # Monday = 0
    # Tuesday = 1
    # ...
    # Friday = 4

    day_map = {
        0: "MON",
        1: "TUE",
        2: "WED",
        3: "THU",
        4: "FRI",
    }


    today_day = day_map.get(
        today.weekday()
    )


    # Saturday / Sunday

    if not today_day:

        return JsonResponse({
            "success": False,
            "message": "There are no classes today."
        })

    # Get Teacher's Schedules
    # For Today


    schedules = Schedule.objects.filter(
        teacher=teacher,
        day=today_day
    ).select_related(
        "class_group",
        "class_group__section",
        "subject",
        "time_slot"
    )


    if not schedules.exists():

        return JsonResponse({
            "success": False,
            "message": "No schedule found for you today."
        })

    # Find Current Time Slot


    current_schedule = None


    for schedule in schedules:

        start_time = schedule.time_slot.start_time
        end_time = schedule.time_slot.end_time


        if start_time <= current_time < end_time:

            current_schedule = schedule
            break

    # No Current Class


    if not current_schedule:

        return JsonResponse({
            "success": False,
            "message": "There is no class scheduled at this time."
        })

    # Section Validation

    student_section_id = student.section_id

    schedule_section_id = (
        current_schedule.class_group.section_id
    )


    if student_section_id != schedule_section_id:

        return JsonResponse({

            "success": False,

            "message":
                f"{student.ID} does not belong to "
                f"{current_schedule.class_group.section}."
        })


    # =========================
    # Save Attendance
    # =========================

    attendance, created = Attendance.objects.update_or_create(

        student=student,

        schedule=current_schedule,

        date=today,

        defaults={
            "status": "PRESENT",
            "method": "QR",
            "remark": "",
        }
    )


    # =========================
    # Response Message
    # =========================

    if created:

        message = (
            f"{student.ID} - "
            f"{student.name} "
            f"Attendance Recorded"
        )

    else:

        message = (
            f"{student.ID} - "
            f"{student.name} "
            f"Attendance Already Recorded"
        )


    # =========================
    # JSON Response
    # =========================

    return JsonResponse({

        "success": True,

        "message": message,

        "student_id": student.ID,

        "student_name": student.name,

        "subject": current_schedule.subject.code,

        "section": str(
            current_schedule.class_group.section
        ),

        "time_slot": str(
            current_schedule.time_slot
        ),

    })
from collections import defaultdict
def count_schedule_occurrences(schedule, start_date, end_date):
    """
    Count how many times a schedule occurs
    between start_date and end_date.
    """

    day_map = {
        'MON': 0,
        'TUE': 1,
        'WED': 2,
        'THU': 3,
        'FRI': 4,
    }
    target_weekday = day_map.get(schedule.day)

    if target_weekday is None:
        return 0

    count = 0
    current = start_date

    while current <= end_date:
        if current.weekday() == target_weekday:
            count += 1

        current += timedelta(days=1)

    return count
@login_required
def attendance_reports(request):
    profile_obj = get_current_teacher_profile(request)
    teacher = request.user.teacher

    section_id = request.GET.get('section')
    subject_id = request.GET.get('subject')
    month = request.GET.get('month')

    today = date.today()

    # SELECTED MONTH

    if month:
        try:
            year, month_number = map(int, month.split('-'))
        except (ValueError, TypeError):
            year = today.year
            month_number = today.month
    else:
        year = today.year
        month_number = today.month

    month_start = date(year, month_number, 1)

    if month_number == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month_number + 1, 1)

    month_end = next_month - timedelta(days=1)

    # TEACHER SCHEDULES

    schedules_qs = (
        Schedule.objects
        .filter(teacher=teacher)
        .select_related(
            'subject',
            'class_group',
            'time_slot'
        )
    )

    if section_id:
        schedules_qs = schedules_qs.filter(
            class_group_id=section_id
        )

    if subject_id:
        schedules_qs = schedules_qs.filter(
            subject_id=subject_id
        )

    # Convert QuerySet to list.
    # We will reuse schedules many times.
    schedules = list(schedules_qs)

    # GROUP SCHEDULES BY SECTION

    schedules_by_section = defaultdict(list)

    for schedule in schedules:
        schedules_by_section[
            schedule.class_group_id
        ].append(schedule)

    # STUDENTS

    students_qs = (
        Student.objects
        .select_related('section')
    )

    if section_id:

        students_qs = students_qs.filter(
            section_id=section_id
        )

    else:

        teacher_section_ids = {
            schedule.class_group_id
            for schedule in schedules
        }

        students_qs = students_qs.filter(
            section_id__in=teacher_section_ids
        )

    students = list(students_qs)

    # ATTENDANCE RECORDS

    # Find all schedules used by these students.
    schedule_ids = [schedule.id for schedule in schedules]

    student_ids = [student.ID for student in students]

    attendance_qs = (
        Attendance.objects
        .filter(
            student_id__in=student_ids,
            schedule_id__in=schedule_ids,
            date__range=(
                date(year, 1, 1),
                date(year, 12, 31)
            )
        )
        .values(
            'student_id',
            'schedule_id',
            'date',
            'status'
        )
    )

    attendance_records = list(attendance_qs)

    # CREATE ATTENDANCE LOOKUP
    # Key:
    # (student_id, schedule_id, month)
    #
    # Value:
    # {
    #     'PRESENT': x,
    #     'LATE': x,
    #     'ABSENT': x
    # }

    attendance_lookup = defaultdict(
        lambda: {
            'PRESENT': 0,
            'LATE': 0,
            'ABSENT': 0
        }
    )

    for record in attendance_records:

        key = (
            record['student_id'],
            record['schedule_id'],
            record['date'].month
        )

        status = record['status']

        if status in attendance_lookup[key]:
            attendance_lookup[key][status] += 1

    # STUDENT PERFORMANCE
    students_performance = []

    for student in students:

        student_schedules = schedules_by_section.get(
            student.section_id,
            []
        )

        expected_classes = 0

        present = 0
        late = 0
        absent = 0

        for schedule in student_schedules:

            expected_classes += count_schedule_occurrences(
                schedule,
                month_start,
                month_end
            )

            key = (
                student.ID,
                schedule.id,
                month_number
            )

            stats = attendance_lookup[key]

            present += stats['PRESENT']
            late += stats['LATE']
            absent += stats['ABSENT']

        attended = present + late

        if expected_classes > 0:

            percentage = (
                attended / expected_classes
            ) * 100

        else:

            percentage = 0

        students_performance.append({
            'student': student,
            'expected': expected_classes,
            'present': present,
            'late': late,
            'absent': absent,
            'attended': attended,
            'percentage': round(percentage, 1),
        })
    # CLASS MONTHLY ATTENDANCE
    monthly_overview = []

    # Pre-calculate students' schedules
    student_schedule_map = {}

    for student in students:

        student_schedule_map[
            student.ID
        ] = schedules_by_section.get(
            student.section_id,
            []
        )

    for month_number_loop in range(1, 13):

        current_month_start = date(
            year,
            month_number_loop,
            1
        )

        if month_number_loop == 12:

            current_next_month = date(
                year + 1,
                1,
                1
            )

        else:

            current_next_month = date(
                year,
                month_number_loop + 1,
                1
            )

        current_month_end = (
            current_next_month - timedelta(days=1)
        )

        expected_total = 0
        attended_total = 0

        for student in students:

            student_schedules = student_schedule_map.get(
                student.ID,
                []
            )

            for schedule in student_schedules:

                expected_total += (
                    count_schedule_occurrences(
                        schedule,
                        current_month_start,
                        current_month_end
                    )
                )

                key = (
                    student.ID,
                    schedule.id,
                    month_number_loop
                )

                stats = attendance_lookup[key]

                attended_total += (
                    stats['PRESENT'] +
                    stats['LATE']
                )

        if expected_total > 0:

            monthly_percentage = (
                attended_total /
                expected_total
            ) * 100

        else:

            monthly_percentage = 0

        monthly_overview.append({
            'month': current_month_start.strftime('%b'),
            'percentage': round(
                monthly_percentage,
                1
            )
        })

    # ATTENDANCE SUMMARY
    total_expected = sum(
        item['expected']
        for item in students_performance
    )

    total_present = sum(
        item['present']
        for item in students_performance
    )

    total_late = sum(
        item['late']
        for item in students_performance
    )

    total_absent = sum(
        item['absent']
        for item in students_performance
    )

    total_attended = (
        total_present +
        total_late
    )

    if total_expected > 0:

        class_average = (
            total_attended /
            total_expected
        ) * 100

    else:

        class_average = 0

    # FILTER OPTIONS


    teacher_schedules = Schedule.objects.filter(
        teacher=teacher
    )

    sections = Section.objects.filter(
        id__in=teacher_schedules.values_list(
            'class_group_id',
            flat=True
        ).distinct()
    )

    subjects = Subject.objects.filter(
        id__in=teacher_schedules.values_list(
            'subject_id',
            flat=True
        ).distinct()
    )

    context = {
        'profile':profile_obj,
        'sections': sections,

        'subjects': subjects,

        'selected_section': section_id,

        'selected_subject': subject_id,

        'selected_month': month,

        'students_performance':
            students_performance,

        'monthly_overview':
            monthly_overview,

        'total_expected':
            total_expected,

        'total_present':
            total_present,

        'total_late':
            total_late,

        'total_absent':
            total_absent,

        'class_average':
            round(
                class_average,
                1
            ),
    }

    return render(
        request,
        'teacher_dashboard/report_view.html',
        context
    )

def section_students(request):
    profile_obj = get_current_teacher_profile(request)
    if not request.user.is_authenticated:
        return redirect('accounts:login')

    teacher = get_object_or_404(
            Teacher,
            user=request.user)

    assignments = TeachingAssignment.objects.filter(
            teacher=teacher).select_related('section')
    context = {
            "profile": profile_obj,
            'teacher': teacher,
            'assignments': assignments,
        }
    return render(
            request,
            'teacher_dashboard/section_students.html',
            context)



def students(request, section_id):
    profile_obj = get_current_teacher_profile(request)
    if not request.user.is_authenticated:
        return redirect('accounts:login')

    teacher = get_object_or_404(
        Teacher,
        user=request.user
    )

    # =========================================================
    # TEACHER'S ASSIGNED SECTIONS
    # =========================================================

    assignments = TeachingAssignment.objects.filter(
        teacher=teacher
    ).select_related(
        'section'
    )

    # Check whether this teacher teaches this section
    assignment = assignments.filter(
        section_id=section_id
    ).first()

    if not assignment:

        context = {
            'teacher': teacher,
            'assignments': assignments,
            'allowed': False,
            'error_message': 'You are not allowed to see this section',
        }

        return render(
            request,
            'teacher_dashboard/students.html',
            context
        )


    # =========================================================
    # MONTH SELECTION
    # =========================================================

    today = date.today()

    try:
        selected_month = int(
            request.GET.get('month', today.month)
        )
    except (TypeError, ValueError):
        selected_month = today.month


    # Only allow valid months
    if selected_month < 1 or selected_month > 12:
        selected_month = today.month


    selected_year = today.year


    month_start = date(
        selected_year,
        selected_month,
        1
    )

    last_day = calendar.monthrange(
        selected_year,
        selected_month
    )[1]

    month_end = date(
        selected_year,
        selected_month,
        last_day
    )


    # =========================================================
    # MONTH LIST
    # =========================================================

    months = []

    for month_number in range(1, 13):

        # Do not show future months
        if (
            selected_year == today.year
            and month_number > today.month
        ):
            continue

        months.append({
            'number': month_number,
            'name': calendar.month_name[month_number],
        })


    # =========================================================
    # STUDENTS
    # =========================================================

    students_qs = Student.objects.filter(
        section_id=section_id,
        is_active=True
    ).order_by(
        'ID'
    )


    # =========================================================
    # SEARCH
    # =========================================================

    search_query = request.GET.get(
        'search',
        ''
    ).strip()


    if search_query:

        students_qs = students_qs.filter(
            Q(ID__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query)
        )


    # =========================================================
    # SCHEDULES FOR THIS SECTION
    # =========================================================

    schedules = Schedule.objects.filter(
        teacher=teacher,
        class_group__section_id=section_id
    ).select_related(
        'subject',
        'class_group',
        'class_group__section',
        'time_slot',
    )


    # =========================================================
    # CALCULATE ATTENDANCE FOR EACH STUDENT
    # =========================================================

    student_list = []


    for student in students_qs:

        # -----------------------------------------------------
        # Expected classes for this student
        # -----------------------------------------------------

        expected = 0


        for schedule in schedules:

            occurrences = count_schedule_occurrences(
                schedule,
                month_start,
                month_end
            )

            expected += occurrences


        # -----------------------------------------------------
        # Actual attended classes
        # PRESENT + LATE
        # -----------------------------------------------------

        attended = Attendance.objects.filter(
            student=student,
            schedule__teacher=teacher,
            schedule__class_group__section_id=section_id,
            date__gte=month_start,
            date__lte=month_end,
            status__in=[
                'PRESENT',
                'LATE'
            ]
        ).values(
            'date',
            'schedule_id'
        ).distinct().count()


        # -----------------------------------------------------
        # Attendance percentage
        # -----------------------------------------------------

        if expected > 0:

            percentage = round(
                (attended / expected) * 100,
                1
            )

            percentage = min(
                percentage,
                100
            )

        else:

            percentage = 0


        # -----------------------------------------------------
        # Attach calculated values
        # -----------------------------------------------------

        student.attendance_percentage = percentage
        student.expected_classes = expected
        student.attended_classes = attended

        student_list.append(student)


    # =========================================================
    # CONTEXT
    # =========================================================

    context = {
        'profile':profile_obj,
        'teacher': teacher,

        'assignments': assignments,

        'assignment': assignment,

        'students': student_list,

        'allowed': True,

        'search_query': search_query,

        'months': months,

        'selected_month': selected_month,

        'selected_year': selected_year,

        'selected_month_name': calendar.month_name[
            selected_month
        ],
    }


    return render(
        request,
        'teacher_dashboard/students.html',
        context
    )


from timetable.models import Attendance, Schedule

from datetime import date, timedelta
from django.core.paginator import Paginator
from django.shortcuts import render



def attendance_history(request):

    profile_obj = get_current_teacher_profile(request)

    selected_class = request.GET.get("class_name", "")
    from_date = request.GET.get("from_date", "")
    to_date = request.GET.get("to_date", "")

    try:
        teacher = request.user.teacher
    except Exception:
        teacher = profile_obj

    # Teacher schedules
    schedules = Schedule.objects.filter(
        teacher=teacher
    ).select_related(
        "class_group",
        "class_group__section",
        "subject",
        "time_slot",
    ).order_by(
        "day",
        "time_slot"
    )

    # Class options
    class_groups = []

    seen_ids = set()

    for schedule in schedules:

        class_group = schedule.class_group

        if class_group and class_group.id not in seen_ids:

            class_groups.append(class_group)
            seen_ids.add(class_group.id)

    # Class filter
    if selected_class:

        try:

            selected_class_id = int(selected_class)

            schedules = schedules.filter(
                class_group_id=selected_class_id
            )

        except (ValueError, TypeError):

            pass

    # DATE RANGE

    if from_date:

        try:
            start_date = date.fromisoformat(from_date)
        except ValueError:
            start_date = date.today()

    else:

        start_date = date.today().replace(
            day=1
        )

    if to_date:

        try:
            end_date = date.fromisoformat(to_date)
        except ValueError:
            end_date = date.today()

    else:

        end_date = date.today()

    # DAY MAP
    day_map = {
        "MON": 0,
        "TUE": 1,
        "WED": 2,
        "THU": 3,
        "FRI": 4,
    }

    # BUILD HISTORY

    history = []

    total_sessions_set = set()

    total_present = 0
    total_late = 0
    total_absent = 0
    total_expected = 0

    for schedule in schedules:

        target_weekday = day_map.get(
            schedule.day
        )

        if target_weekday is None:
            continue

        current_date = start_date

        while current_date <= end_date:

            if current_date.weekday() != target_weekday:

                current_date += timedelta(days=1)
                continue

            # One class session
            total_sessions_set.add(
                (
                    current_date,
                    schedule.id
                )
            )

            section = schedule.class_group.section

            # Students in this section
            students = Student.objects.filter(
                section=section,
                is_active=True
            ).order_by(
                "ID"
            )

            for student in students:

                # Approved leave
                if student_on_leave(
                    student,
                    current_date
                ):
                    continue

                total_expected += 1

                attendance = Attendance.objects.filter(
                    student=student,
                    schedule=schedule,
                    date=current_date
                ).first()

                # ATTENDANCE STATUS


                if attendance:

                    status = attendance.status

                    if status == "PRESENT":
                        total_present += 1

                    elif status == "LATE":
                        total_late += 1

                    elif status == "ABSENT":
                        total_absent += 1

                else:

                    # No attendance record
                    # = Absent
                    status = "ABSENT"

                    total_absent += 1

                # --------------------------------------
                # HISTORY ROW
                # --------------------------------------

                history.append({
                    "date": current_date,
                    "student": student,
                    "schedule": schedule,
                    "status": status,
                    "method": (
                        attendance.method
                        if attendance
                        else "-"
                    ),
                    "remark": (
                        attendance.remark
                        if attendance
                        else "No Attendance"
                    ),
                })

            current_date += timedelta(days=1)

    # TOTAL CLASS SESSIONS

    total_sessions = len(
        total_sessions_set
    )

    # PAGINATION
    history.sort(
        key=lambda x: (
            x["date"],
            x["schedule"].time_slot.start_time
        ),
        reverse=True
    )

    paginator = Paginator(
        history,
        10
    )

    page_number = request.GET.get(
        "page",
        1
    )

    page_obj = paginator.get_page(
        page_number
    )

    context = {

        "profile": profile_obj,

        "class_groups": class_groups,

        "selected_class": selected_class,

        "from_date": from_date,

        "to_date": to_date,

        "total_sessions": total_sessions,

        "total_expected": total_expected,

        "total_present": total_present,

        "total_absent": total_absent,

        "total_late": total_late,

        "total_records": len(history),

        "page_obj": page_obj,

        "total_count": paginator.count,
    }

    return render(
        request,
        "teacher_dashboard/attendance_history_view.html",
        context
    )
@login_required
def teacher_attendance(request, schedule_id):
    profile_obj = get_current_teacher_profile(request)
    try:
        teacher = request.user.teacher
    except Teacher.DoesNotExist:
        messages.error(request, "Teacher profile not found.")
        return redirect('home')

    # Only this teacher's schedule
    schedule = get_object_or_404(
        Schedule,
        id=schedule_id,
        teacher=teacher
    )

    # Attendance Date

    selected_date = (
        request.POST.get('attendance_date')
        if request.method == 'POST'
        else request.GET.get('attendance_date')
    )

    if selected_date:
        try:
            attendance_date = date.fromisoformat(selected_date)
        except (ValueError, TypeError):
            attendance_date = date.today()
    else:
        attendance_date = date.today()

    # -----------------------------
    # Students in this Schedule's Section
    # -----------------------------

    students = Student.objects.filter(
        section=schedule.class_group.section,
        is_active=True
    ).order_by('ID')

    # Existing Attendance

    existing_attendance = {
        attendance.student_id: attendance
        for attendance in Attendance.objects.filter(
            schedule=schedule,
            date=attendance_date
        )
    }

    # POST - Save Attendance

    if request.method == 'POST':

        with transaction.atomic():

            for student in students:

                status = request.POST.get(
                    f'status_{student.ID}'
                )

                remark = request.POST.get(
                    f'remark_{student.ID}',
                    ''
                ).strip()

                if status not in ['PRESENT', 'ABSENT', 'LATE']:
                    continue

                Attendance.objects.update_or_create(

                    student=student,

                    schedule=schedule,

                    date=attendance_date,

                    defaults={
                        'status': status,
                        'method': 'MANUAL',
                        'remark': remark,
                    }
                )

        messages.success(
            request,
            f"Attendance saved successfully for "
            f"{attendance_date.strftime('%d-%m-%Y')}."
        )

        return redirect(
            'teacher_dashboard:teacher_attendance',
            schedule_id=schedule.id
        )

    # Prepare students for template

    student_rows = []

    for student in students:

        attendance = existing_attendance.get(student.ID)

        student_rows.append({
            'student': student,
            'attendance': attendance,
            'status': attendance.status if attendance else '',
            'remark': attendance.remark if attendance else '',
        })

    context = {
        "profile":profile_obj,
        'schedule': schedule,
        'students': student_rows,
        'attendance_date': attendance_date,
        'schedule_id': schedule.id,
    }

    return render(
        request,
        'teacher_dashboard/takeattendance.html',
        context
    )
from timetable.utils import student_on_leave

def manual_attendance(request):
    profile_obj = get_current_teacher_profile(request)
    teacher = get_object_or_404(
        Teacher,
        user=request.user
    )

    # TEACHER'S SCHEDULES

    schedules = Schedule.objects.filter(
        teacher=teacher
    ).select_related(
        'class_group',
        'class_group__section',
        'subject',
        'time_slot'
    ).order_by(
        'day',
        'time_slot'
    )

    # TEACHER'S SECTIONS

    section_ids = schedules.values_list(
        'class_group__section_id',
        flat=True
    ).distinct()

    sections = Section.objects.filter(
        id__in=section_ids
    ).order_by(
        'sem',
        'name'
    )

    # GET / POST VALUES

    attendance_date = (
        request.GET.get('attendance_date')
        or request.POST.get('attendance_date')
    )

    selected_section_id = (
        request.GET.get('section_id')
        or request.POST.get('section_id')
    )

    selected_schedule_id = (
        request.GET.get('schedule_id')
        or request.POST.get('schedule_id')
    )


    selected_date = None


    # VALIDATE DATE

    if attendance_date:

        try:

            selected_date = date.fromisoformat(
                attendance_date
            )

        except ValueError:

            messages.error(
                request,
                "Invalid attendance date."
            )

            attendance_date = ''
            selected_date = None

    # WEEKEND CHECK

    if selected_date:

        if selected_date.weekday() in [5, 6]:

            messages.error(
                request,
                "Attendance can only be taken from Monday to Friday."
            )

            attendance_date = ''
            selected_date = None

    # SELECTED SCHEDULE

    schedule = None
    section = None
    students = []


    if selected_schedule_id:

        schedule = get_object_or_404(
            schedules,
            id=selected_schedule_id
        )

        section = schedule.class_group.section

        # CHECK SECTION

        if selected_section_id:

            if str(section.id) != str(selected_section_id):

                messages.error(
                    request,
                    "Selected section does not match the schedule."
                )

                return redirect(
                    'teacher_dashboard:manual_attendance'
                )

        # CHECK DATE AGAINST TIMETABLE

        if selected_date:

            # Example:
            # Monday  -> MON
            # Tuesday -> TUE
            # Wednesday -> WED

            selected_day = (
                selected_date
                .strftime('%a')
                .upper()
            )

            schedule_day = (
                schedule.day
                .upper()
            )


            # Date and timetable must match

            if selected_day != schedule_day:

                messages.error(
                    request,
                    f"{selected_date.strftime('%d %b %Y')} is "
                    f"{selected_date.strftime('%A')}. "
                    f"This class is scheduled on "
                    f"{schedule.get_day_display()}."
                )

                return redirect(
                    'teacher_dashboard:manual_attendance'
                )

        # LOAD STUDENTS

        if selected_date:

            students_qs = Student.objects.filter(
                section=section,
                is_active=True
            ).order_by(
                'ID'
            )


            for student in students_qs:

                # Approved Leave

                if student_on_leave(
                    student,
                    selected_date
                ):
                    continue


                attendance = Attendance.objects.filter(
                    student=student,
                    schedule=schedule,
                    date=selected_date
                ).first()


                students.append({

                    'student': student,

                    'status': (
                        attendance.status
                        if attendance
                        else 'ABSENT'
                    ),

                    'remark': (
                        attendance.remark
                        if attendance
                        else ''
                    ),

                })

    # POST - SAVE ATTENDANCE

    if request.method == 'POST':

        if not schedule or not section:

            messages.error(
                request,
                "Please select a schedule first."
            )

            return redirect(
                'teacher_dashboard:manual_attendance'
            )


        if not selected_date:

            messages.error(
                request,
                "Please select a valid attendance date."
            )

            return redirect(
                'teacher_dashboard:manual_attendance'
            )


        # IMPORTANT:
        # CHECK DATE VS TIMETABLE AGAIN BEFORE SAVING

        selected_day = (
            selected_date
            .strftime('%a')
            .upper()
        )

        schedule_day = (
            schedule.day
            .upper()
        )


        if selected_day != schedule_day:

            messages.error(
                request,
                f"Cannot save attendance. "
                f"{selected_date.strftime('%d %b %Y')} is "
                f"{selected_date.strftime('%A')}, but this class "
                f"is scheduled on {schedule.get_day_display()}."
            )

            return redirect(
                'teacher_dashboard:manual_attendance'
            )

        # SAVE STUDENTS

        students_qs = Student.objects.filter(
            section=section,
            is_active=True
        ).order_by(
            'ID'
        )


        for student in students_qs:

            # Approved Leave

            if student_on_leave(
                student,
                selected_date
            ):
                continue


            status = request.POST.get(
                f'status_{student.ID}'
            )

            remark = request.POST.get(
                f'remark_{student.ID}',
                ''
            ).strip()


            # IMPORTANT:
            # LATE is also allowed

            if status not in [
                'PRESENT',
                'ABSENT'
            ]:
                continue


            Attendance.objects.update_or_create(

                student=student,

                schedule=schedule,

                date=selected_date,

                defaults={
                    'status': status,
                    'method': 'MANUAL',
                    'remark': remark,
                }
            )


        messages.success(
            request,
            "Manual attendance saved successfully."
        )

        return redirect(
            'teacher_dashboard:manual_attendance'
        )

    # DAY FOR DISPLAY

    attendance_day = None

    if selected_date:

        attendance_day = selected_date.strftime(
            '%A'
        )

    context = {
        'profile':profile_obj,
        'teacher': teacher,

        'schedules': schedules,

        'sections': sections,

        'schedule': schedule,

        'section': section,

        'students': students,

        'attendance_date': selected_date,

        'attendance_day': attendance_day,

        'selected_section_id': selected_section_id,

        'selected_schedule_id': selected_schedule_id,

    }


    return render(
        request,
        'teacher_dashboard/manual_attendance.html',
        context
    )
def teacher_attendance_list(request):
    profile_obj = get_current_teacher_profile(request)
    try:
        teacher = request.user.teacher

    except Teacher.DoesNotExist:
        messages.error(request, "Teacher profile not found.")
        return redirect('teacher_dashboard:teacher_dashboard')

    attendance_records = Attendance.objects.filter(
        schedule__teacher=teacher
    ).select_related(
        'student',
        'schedule',
        'schedule__subject',
        'schedule__class_group',
        'schedule__time_slot',
        'schedule__teacher',
    ).order_by(
        '-date',
        'schedule__time_slot__start_time',
        'student__ID'
    )

    selected_date = request.GET.get('date')
    selected_subject = request.GET.get('subject')


    if selected_date:

        attendance_records = attendance_records.filter(
            date=selected_date
        )


    if selected_subject:

        attendance_records = attendance_records.filter(
            schedule__subject_id=selected_subject
        )

    subjects = Subject.objects.filter(
        schedule__teacher=teacher
    ).distinct()

    # တစ် page မှာ attendance 5 ခု
    paginator = Paginator(attendance_records, 5)

    page_number = request.GET.get('page', 1)

    page_obj = paginator.get_page(page_number)

    context = {
        'profile': profile_obj,
        'attendance_records': page_obj,

        'page_obj': page_obj,

        'paginator': paginator,

        'subjects': subjects,

        'selected_date': selected_date,

        'selected_subject': selected_subject,

    }


    return render(
        request,
        'teacher_dashboard/attendance_schedule_list.html',
        context
    )
@login_required
def attendance_report(request):
    profile_obj = get_current_teacher_profile(request)
    teacher = request.user.teacher

    # ==================================================
    # FILTERS
    # ==================================================

    subject_id = request.GET.get('subject')
    section_id = request.GET.get('section')
    month = request.GET.get('month')

    # ==================================================
    # DATE RANGE
    # ==================================================

    today = timezone.localdate()

    if month:
        year, month_number = map(int, month.split('-'))
    else:
        year = today.year
        month_number = today.month
        month = f"{year:04d}-{month_number:02d}"

    start_date = date(
        year,
        month_number,
        1
    )

    end_date = date(
        year,
        month_number,
        calendar.monthrange(
            year,
            month_number
        )[1]
    )

    # ==================================================
    # TEACHER'S SCHEDULES
    # ==================================================

    schedules = Schedule.objects.filter(
        teacher=teacher
    ).select_related(
        'subject',
        'class_group',
        'class_group__section',
        'time_slot',
    )

    # Subject filter
    if subject_id:
        schedules = schedules.filter(
            subject_id=subject_id
        )

    # Section filter
    if section_id:
        schedules = schedules.filter(
            class_group__section_id=section_id
        )

    # ==================================================
    # ATTENDANCE RECORDS
    # ==================================================

    attendance_qs = Attendance.objects.filter(
        schedule__in=schedules,
        date__range=(
            start_date,
            end_date
        )
    ).select_related(
        'student',
        'schedule',
        'schedule__subject',
        'schedule__class_group',
        'schedule__class_group__section',
    )

    # ==================================================
    # STUDENTS
    # ==================================================

    teacher_section_ids = schedules.values_list(
        'class_group__section_id',
        flat=True
    ).distinct()

    student_qs = Student.objects.filter(
        is_active=True,
        section_id__in=teacher_section_ids
    ).select_related(
        'section'
    ).order_by('ID')

    if section_id:
        student_qs = student_qs.filter(
            section_id=section_id
        )

    # ==================================================
    # ATTENDANCE LOOKUP
    # ==================================================

    attendance_lookup = {}

    for attendance in attendance_qs:

        key = (
            attendance.student_id,
            attendance.schedule_id,
            attendance.date
        )

        attendance_lookup[key] = attendance

    # ==================================================
    # DAY MAPPING
    # ==================================================

    day_map = {
        'MON': 0,
        'TUE': 1,
        'WED': 2,
        'THU': 3,
        'FRI': 4,
    }

    student_data = {}

    for student in student_qs:

        student_data[student.ID] = {
            'student': student,

            'expected': 0,

            'present': 0,

            'late': 0,

            'absent': 0,

            'total': 0,

            'attended': 0,

            'percentage': 0,
        }

    for student in student_qs:

        data = student_data[student.ID]

        # Student's section schedules only
        student_schedules = schedules.filter(
            class_group__section_id=student.section_id
        )

        for schedule in student_schedules:

            schedule_weekday = day_map.get(
                schedule.day
            )

            # Ignore invalid / weekend schedule
            if schedule_weekday is None:
                continue

            current_date = start_date

            while current_date <= end_date:

                if current_date.weekday() == schedule_weekday:

                    # ----------------------------------
                    # Approved leave
                    # ----------------------------------

                    if student_on_leave(
                        student,
                        current_date
                    ):
                        current_date += timezone.timedelta(
                            days=1
                        )
                        continue

                    # ----------------------------------
                    # Expected class
                    # ----------------------------------

                    data['expected'] += 1

                    key = (
                        student.ID,
                        schedule.id,
                        current_date
                    )

                    attendance = attendance_lookup.get(
                        key
                    )

                    # ----------------------------------
                    # Attendance status
                    # ----------------------------------

                    if attendance:

                        if attendance.status == 'PRESENT':
                            data['present'] += 1

                        elif attendance.status == 'LATE':
                            data['late'] += 1

                        elif attendance.status == 'ABSENT':
                            data['absent'] += 1

                    else:
                        # No attendance record
                        # = absent
                        data['absent'] += 1

                current_date += timezone.timedelta(
                    days=1
                )

        # ----------------------------------------------
        # Total attendance
        # ----------------------------------------------

        data['total'] = data['expected']

        # ----------------------------------------------
        # Attended
        # ----------------------------------------------

        data['attended'] = (
            data['present']
            + data['late']
        )

        # ----------------------------------------------
        # Percentage
        # ----------------------------------------------

        if data['expected'] > 0:

            data['percentage'] = (
                data['attended']
                / data['expected']
            ) * 100

        else:

            data['percentage'] = 0

    # ==================================================
    # ATTENDANCE SUMMARY
    # ==================================================

    # --------------------------------------------------
    # TOTAL CLASSES
    #
    # Count scheduled class occurrences.
    # NOT multiplied by number of students.
    # --------------------------------------------------

    total_expected = 0

    for schedule in schedules:

        schedule_weekday = day_map.get(
            schedule.day
        )

        if schedule_weekday is None:
            continue

        current_date = start_date

        while current_date <= end_date:

            if current_date.weekday() == schedule_weekday:

                total_expected += 1

            current_date += timezone.timedelta(
                days=1
            )

    # --------------------------------------------------
    # PRESENT
    # --------------------------------------------------

    total_present = sum(
        data['present']
        for data in student_data.values()
    )

    # --------------------------------------------------
    # LATE
    # --------------------------------------------------

    total_late = sum(
        data['late']
        for data in student_data.values()
    )

    # --------------------------------------------------
    # ABSENT
    # --------------------------------------------------

    total_absent = sum(
        data['absent']
        for data in student_data.values()
    )

    # --------------------------------------------------
    # CLASS AVERAGE
    # --------------------------------------------------

    percentages = [
        data['percentage']
        for data in student_data.values()
        if data['expected'] > 0
    ]

    if percentages:

        class_average = (
            sum(percentages)
            / len(percentages)
        )

    else:

        class_average = 0

    subjects = teacher.subj.all().order_by(
        'code'
    )

    sections = Section.objects.filter(
        id__in=teacher_section_ids
    ).order_by(
        'sem',
        'name'
    )

    context = {

        # Student data
        'student_data': student_data.values(),

        'students_performance': student_data.values(),
        'profile':profile_obj,
        # Subjects
        'subjects': subjects,

        # Sections
        'sections': sections,

        # Filters
        'selected_subject': subject_id,

        'selected_section': section_id,

        'selected_month': month,

        # Dates
        'start_date': start_date,

        'end_date': end_date,

        # Attendance Summary
        'total_expected': total_expected,

        'total_present': total_present,

        'total_late': total_late,

        'total_absent': total_absent,

        'class_average': class_average,
    }

    return render(
        request,
        'teacher_dashboard/report_view.html',
        context={'profile':profile_obj}
    )
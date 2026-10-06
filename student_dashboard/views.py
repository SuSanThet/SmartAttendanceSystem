from types import SimpleNamespace

from django.contrib import messages
from django.shortcuts import render, redirect,get_object_or_404
from admin_dashboard.models import Student
from .models import Profile

from django.contrib.auth.decorators import login_required
from timetable.models import TimeSlot, Schedule, AcademicClass
from admin_dashboard.models import LeaveRequest

@login_required
def get_current_student_profile(request):
    if not request.user.is_authenticated:
        return None

    student = Student.objects.filter(
        user=request.user
    ).first()

    if not student:
        return None

    profile_obj, _ = Profile.objects.get_or_create(
        student=student
    )
    return profile_obj

@login_required
def student_dashboard_preview(request):

    profile_obj = get_current_student_profile(request)
    student = request.user.student

    today = timezone.localdate()
    student_section = student.section

    # All schedules for student's section
    section_schedules = Schedule.objects.filter(
        class_group__section=student_section
    ).select_related(
        "subject",
        "teacher",
        "time_slot",
        "class_group",
        "class_group__section"
    ).order_by(
        "time_slot__start_time"
    )

    # Today's classes
    todays_classes = []

    # Check student leave
    today_on_leave = student_on_leave(
        student,
        today
    )

    if today.weekday() in [5, 6]:

        is_holiday = True

    elif today_on_leave:

        is_holiday = False

        todays_classes.append({
            "time": "",
            "code": "",
            "subject": "You are on leave",
            "name": "",
            "teacher": "",
            "status": "Leave",
        })

    else:

        is_holiday = False

        day_map = {
            0: "MON",
            1: "TUE",
            2: "WED",
            3: "THU",
            4: "FRI",
        }

        today_code = day_map[today.weekday()]

        todays_schedules = section_schedules.filter(
            day=today_code
        )

        current_time = timezone.localtime().time()

        for schedule in todays_schedules:

            start_time = schedule.time_slot.start_time
            end_time = schedule.time_slot.end_time

            attendance = Attendance.objects.filter(
                student=student,
                schedule=schedule,
                date=today
            ).first()

            if attendance:

                status = attendance.status

            elif current_time < start_time:

                status = "Upcoming"

            elif start_time <= current_time <= end_time:

                status = "Ongoing"

            else:

                status = "Completed"

            todays_classes.append({
                "time": (
                    f"{start_time.strftime('%H:%M')} - "
                    f"{end_time.strftime('%H:%M')}"
                ),
                "code": schedule.subject.code,
                "subject": schedule.subject.name,
                "name": str(schedule.class_group),
                "teacher": schedule.teacher.TrID,
                "status": status,
            })

    # Current month
    year = today.year
    month = today.month

    month_start = date(
        year,
        month,
        1
    )

    if month == 12:

        next_month = date(
            year + 1,
            1,
            1
        )

    else:

        next_month = date(
            year,
            month + 1,
            1
        )

    month_end = next_month - timedelta(days=1)

    # Attendance
    attendance_qs = Attendance.objects.filter(
        student=student,
        date__range=(
            month_start,
            month_end
        )
    ).select_related(
        "schedule",
        "schedule__subject"
    )

    present = attendance_qs.filter(
        status="PRESENT"
    ).count()

    late = attendance_qs.filter(
        status="LATE"
    ).count()

    attended = present + late

    # Expected classes
    expected = 0

    for schedule in section_schedules:

        expected += get_student_expected_classes(
            student,
            schedule,
            month_start,
            month_end
        )

    # Remaining classes are treated as absent
    absent = max(
        expected - attended,
        0
    )

    # Attendance rate
    if expected > 0:

        attendance_rate = round(
            (attended / expected) * 100,
            1
        )

    else:

        attendance_rate = 0

    # Recent attendance
    recent_attendance = Attendance.objects.filter(
        student=student
    ).select_related(
        "schedule",
        "schedule__subject"
    ).order_by(
        "-date",
        "-id"
    )[:5]

    # Monthly chart
    monthly_data = []

    month_names = [
        "Jan", "Feb", "Mar", "Apr",
        "May", "Jun", "Jul", "Aug",
        "Sep", "Oct", "Nov", "Dec"
    ]

    for m in range(1, 13):

        current_month_start = date(
            year,
            m,
            1
        )

        if m == 12:

            current_next_month = date(
                year + 1,
                1,
                1
            )

        else:

            current_next_month = date(
                year,
                m + 1,
                1
            )

        current_month_end = (
            current_next_month -
            timedelta(days=1)
        )

        # Expected classes
        expected_month = 0

        for schedule in section_schedules:

            expected_month += (
                get_student_expected_classes(
                    student,
                    schedule,
                    current_month_start,
                    current_month_end
                )
            )

        # Attendance for this month
        month_attendance = Attendance.objects.filter(
            student=student,
            date__range=(
                current_month_start,
                current_month_end
            )
        )

        month_present = month_attendance.filter(
            status="PRESENT"
        ).count()

        month_late = month_attendance.filter(
            status="LATE"
        ).count()

        month_attended = (
            month_present +
            month_late
        )

        if expected_month > 0:

            percentage = round(
                (
                    month_attended /
                    expected_month
                ) * 100,
                1
            )

        else:

            percentage = 0

        monthly_data.append({
            "label": month_names[m - 1],
            "percentage": percentage,
            "expected": expected_month,
            "attended": month_attended,
            "is_current": m == month,
        })

    context = {
        "profile": profile_obj,

        "present": present,
        "late": late,
        "absent": absent,
        "attended": attended,
        "expected": expected,
        "attendance_rate": attendance_rate,

        "todays_classes": todays_classes,
        "is_holiday": is_holiday,
        "today_on_leave": today_on_leave,

        "recent_attendance": recent_attendance,

        "monthly_data": monthly_data,
    }

    return render(
        request,
        "student_dashboard/dashboard.html",
        context
    )
def student_profile(request):
    profile_obj = get_current_student_profile(request)
    student=Student.objects.get(user=request.user)

    if request.method == 'POST':

        if 'profile_pic' in request.FILES:
            profile_obj.profile_pic = request.FILES['profile_pic']
            profile_obj.save()
            return redirect('student_dashboard:profile') # သင့် profile url name အတိုင်း ပြန်ညွှန်းပါ

      
        if 'delete_pic' in request.POST:
            if profile_obj.profile_pic:
                profile_obj.profile_pic.delete(save=True)
            return redirect('student_dashboard:profile')

    return render(request, 'student_dashboard/profile.html', {'profile': profile_obj,'student':student})

def my_attendance(request):

    profile_obj = get_current_student_profile(request)

    student = request.user.student
#selected month
    month = request.GET.get('month')

    today = date.today()

    if month:
        try:
            year, month_number = map(
                int,
                month.split('-')
            )
        except (ValueError, TypeError):
            year = today.year
            month_number = today.month
    else:
        year = today.year
        month_number = today.month
#att rec
    attendance_records = Attendance.objects.filter(
        student=student,
        date__year=year,
        date__month=month_number
    ).select_related(
        'schedule',
        'schedule__subject',
        'schedule__teacher'
    ).order_by(
        '-date',
        '-schedule__time_slot'
    )

    context = {

        'profile': profile_obj,

        'attendance_records':
            attendance_records,

        'selected_month':
            f'{year:04d}-{month_number:02d}',

    }


    return render(
        request,
        'student_dashboard/my_attendance.html',
        context
    )
def myqr_view(request):
    profile_obj = get_current_student_profile(request)
    student = Student.objects.get(user=request.user)

    return render(request, "student_dashboard/myqr.html", {
        "profile":profile_obj,"student": student
    })
"""  if request.method == "GET":
        ID = request.GET.get("ID")
        if ID:
            student = get_object_or_404(Student, ID=ID)"""
@login_required
def student_timetable(request):
    profile_obj = get_current_student_profile(request)
    student = request.user.student

    selected_class = None
    grid = []

    time_slots = TimeSlot.objects.all()

    if student.section:
        selected_class = AcademicClass.objects.filter(
            section=student.section,
            major=student.major
        ).first()

    if selected_class:
        entries = Schedule.objects.filter(
            class_group=selected_class
        ).select_related(
            'subject',
            'teacher',
            'time_slot'
        )

        lookup = {
            (entry.day, entry.time_slot_id): entry
            for entry in entries
        }

        for slot in time_slots:
            row = {
                'time_slot': slot,
                'cells': []
            }

            for day_code, day_label in Schedule.DAY_CHOICES:
                row['cells'].append({
                    'day': day_code,
                    'day_label': day_label,
                    'entry': lookup.get(
                        (day_code, slot.id)
                    ),
                })

            grid.append(row)

    context = {
        'profile':profile_obj,
        'student': student,
        'selected_class': selected_class,
        'time_slots': time_slots,
        'grid': grid,
    }

    return render(
        request,
        'student_dashboard/mysection.html',
        context
    )

from datetime import date, timedelta

from timetable.models import Attendance, Schedule,AcademicClass

def count_schedule_occurrences(schedule, start_date, end_date):

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

from datetime import date, timedelta

from timetable.utils import get_student_expected_classes, student_on_leave


@login_required
def attendance_statistics(request):
    profile_obj = get_current_student_profile(request)
    student = request.user.student
    section = student.section

    month = request.GET.get('month')

    today = date.today()

    # Month
    if month:

        try:
            year, month_number = map(
                int,
                month.split('-')
            )

        except (ValueError, TypeError):

            year = today.year
            month_number = today.month

    else:

        year = today.year
        month_number = today.month

    # Month start / end
    month_start = date(
        year,
        month_number,
        1
    )

    if month_number == 12:

        next_month = date(
            year + 1,
            1,
            1
        )

    else:

        next_month = date(
            year,
            month_number + 1,
            1
        )

    month_end = next_month - timedelta(days=1)

    # Find academic class
    academic_class = AcademicClass.objects.filter(
        section=section
    ).first()

    # No academic class
    if not academic_class:

        context = {
            'student': student,
            'section': section,
            'expected': 0,
            'total': 0,
            'present': 0,
            'late': 0,
            'absent': 0,
            'attended': 0,
            'percentage': 0,
            'present_percentage': 0,
            'subjects': [],
            'monthly_data': [],
            'selected_month': month,
        }

        return render(
            request,
            'student_dashboard/attendance_statistics.html',
            context
        )

    # Schedules for student's class
    schedules = Schedule.objects.filter(
        class_group=academic_class
    ).select_related(
        'subject',
        'time_slot'
    )

    # Attendance for selected month
    attendance_qs = Attendance.objects.filter(
        student=student,
        date__range=(
            month_start,
            month_end
        )
    ).select_related(
        'schedule',
        'schedule__subject',
        'schedule__time_slot'
    )

    # Expected classes
    expected = 0

    for schedule in schedules:

        expected += get_student_expected_classes(
            student,
            schedule,
            month_start,
            month_end
        )

    # Attendance
    present = attendance_qs.filter(
        status='PRESENT'
    ).count()

    late = attendance_qs.filter(
        status='LATE'
    ).count()

    attended = present + late

    # Absent
    absent = max(
        expected - attended,
        0
    )

    # Overall percentage
    if expected > 0:

        percentage = (
            attended / expected
        ) * 100

    else:

        percentage = 0

    present_percentage = percentage

    # Subject breakdown
    subjects = []

    subject_ids = schedules.values_list(
        'subject_id',
        flat=True
    ).distinct()

    for subject_id in subject_ids:

        subject_schedules = schedules.filter(
            subject_id=subject_id
        )

        # Expected subject classes
        subject_expected = 0

        for schedule in subject_schedules:

            subject_expected += (
                get_student_expected_classes(
                    student,
                    schedule,
                    month_start,
                    month_end
                )
            )

        # Attendance records
        records = attendance_qs.filter(
            schedule__subject_id=subject_id
        )

        subject_present = records.filter(
            status='PRESENT'
        ).count()

        subject_late = records.filter(
            status='LATE'
        ).count()

        subject_attended = (
            subject_present +
            subject_late
        )

        # Subject absent
        subject_absent = max(
            subject_expected - subject_attended,
            0
        )

        if subject_expected > 0:

            subject_percentage = (
                subject_attended /
                subject_expected
            ) * 100

        else:

            subject_percentage = 0

        subject = (
            subject_schedules
            .first()
            .subject
        )

        subjects.append({

            'subject': subject,

            'expected': subject_expected,

            'present': subject_present,

            'late': subject_late,

            'absent': subject_absent,

            'attended': subject_attended,

            'total': subject_expected,

            'percentage': round(
                subject_percentage,
                1
            ),

        })

    # Monthly data
    monthly_data = []

    month_names = [
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

    for month_loop in range(1, 13):

        current_month_start = date(
            year,
            month_loop,
            1
        )

        if month_loop == 12:

            current_next_month = date(
                year + 1,
                1,
                1
            )

        else:

            current_next_month = date(
                year,
                month_loop + 1,
                1
            )

        current_month_end = (
            current_next_month -
            timedelta(days=1)
        )

        # Expected
        month_expected = 0

        for schedule in schedules:

            month_expected += (
                get_student_expected_classes(
                    student,
                    schedule,
                    current_month_start,
                    current_month_end
                )
            )

        # Attendance
        month_records = Attendance.objects.filter(
            student=student,
            date__range=(
                current_month_start,
                current_month_end
            )
        )

        month_present = month_records.filter(
            status='PRESENT'
        ).count()

        month_late = month_records.filter(
            status='LATE'
        ).count()

        month_attended = (
            month_present +
            month_late
        )

        # Percentage
        if month_expected > 0:

            month_percentage = (
                month_attended /
                month_expected
            ) * 100

        else:

            month_percentage = 0

        is_current = (
            month_loop == month_number
        )

        monthly_data.append({

            'label':
                month_names[
                    month_loop - 1
                ],

            'percentage':
                round(
                    month_percentage,
                    1
                ),

            'expected':
                month_expected,

            'attended':
                month_attended,

            'present':
                month_present,

            'late':
                month_late,

            'is_current':
                is_current,

        })

    context = {
        'profile':profile_obj,
        'student': student,

        'section': section,

        'expected': expected,

        'total': expected,

        'present': present,

        'late': late,

        'absent': absent,

        'attended': attended,

        'percentage': round(
            percentage,
            1
        ),

        'present_percentage': round(
            present_percentage,
            1
        ),

        'subjects': subjects,

        'monthly_data': monthly_data,

        'selected_month': month,

    }

    return render(
        request,
        'student_dashboard/attendance_statistics.html',
        context
    )
from datetime import date
from django.utils import timezone
from django.contrib import messages


def leave_request(request):
    profile_obj = get_current_student_profile(request)

    student = profile_obj.student
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
        "student_dashboard/leave_request.html",
        {
            'profile': profile_obj,
            "leave_requests": leave_requests,
        }
    )


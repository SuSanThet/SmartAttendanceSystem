from datetime import timedelta

from admin_dashboard.models import LeaveRequest


def student_on_leave(student, attendance_date):
    return LeaveRequest.objects.filter(
        requester=student.user,
        status="APPROVED",
        start_date__lte=attendance_date,
        end_date__gte=attendance_date,
    ).exists()

def get_student_leave_dates(student, start_date, end_date):

    leaves = LeaveRequest.objects.filter(
        requester=student.user,
        status="APPROVED",
        start_date__lte=end_date,
        end_date__gte=start_date,
    )

    leave_dates = set()

    for leave in leaves:

        current_date = max(
            leave.start_date,
            start_date
        )

        leave_end = min(
            leave.end_date,
            end_date
        )

        while current_date <= leave_end:

            leave_dates.add(current_date)

            current_date += timedelta(days=1)

    return leave_dates

def get_schedule_dates(
    schedule,
    start_date,
    end_date
):

    day_map = {
        "MON": 0,
        "TUE": 1,
        "WED": 2,
        "THU": 3,
        "FRI": 4,
    }

    target_weekday = day_map[schedule.day]

    schedule_dates = []

    current_date = start_date

    while current_date <= end_date:

        if current_date.weekday() == target_weekday:
            schedule_dates.append(current_date)

        current_date += timedelta(days=1)

    return schedule_dates
def get_student_expected_classes(
    student,
    schedule,
    start_date,
    end_date
):

    schedule_dates = get_schedule_dates(
        schedule,
        start_date,
        end_date
    )

    leave_dates = get_student_leave_dates(
        student,
        start_date,
        end_date
    )

    actual_expected = 0

    for class_date in schedule_dates:

        if class_date in leave_dates:
            continue

        actual_expected += 1

    return actual_expected
from django.core.management.base import BaseCommand
from django.utils import timezone

from admin_dashboard.models import LeaveRequest


class Command(BaseCommand):

    help = "Update active status based on approved leave requests"

    def handle(self, *args, **kwargs):

        today = timezone.localdate()

        approved_leaves = LeaveRequest.objects.filter(
            status="APPROVED"
        ).select_related("requester")

        for leave in approved_leaves:

            user = leave.requester

            if leave.start_date <= today <= leave.end_date:

                if hasattr(user, "student"):

                    student = user.student

                    if student.is_active:
                        student.is_active = False
                        student.save(
                            update_fields=["is_active"]
                        )

                elif hasattr(user, "teacher"):

                    teacher = user.teacher

                    if teacher.is_active:
                        teacher.is_active = False
                        teacher.save(
                            update_fields=["is_active"]
                        )

            elif today > leave.end_date:

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

        self.stdout.write(
            self.style.SUCCESS(
                "Leave status updated successfully."
            )
        )
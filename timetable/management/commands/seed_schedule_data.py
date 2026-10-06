from datetime import time

from django.core.management.base import BaseCommand

from timetable.models import Department, TimeSlot


class Command(BaseCommand):
    help = 'Seeds default departments and time slots for the scheduler.'

    def handle(self, *args, **kwargs):
        departments = [
            ('Software Engineering', 'SE'),
            ('Knowledge Engineering', 'KE'),
            ('High Performance Computing', 'HPC'),
            ('Network / Computer Technology', 'CT'),
            ('Communication and Fintech Systems', 'CFS'),
            ('Business Information Systems', 'BIS'),
        ]
        for name, code in departments:
            Department.objects.get_or_create(short_code=code, defaults={'name': name})

        periods = [
            (time(9, 0), time(10, 0)),
            (time(10, 0), time(11, 0)),
            (time(11, 0), time(12, 0)),
            (time(13, 0), time(14, 0)),
            (time(14, 0), time(15, 0)),
            (time(15, 0), time(16, 0)),
        ]
        for start, end in periods:
            TimeSlot.objects.get_or_create(start_time=start, end_time=end)

        self.stdout.write(self.style.SUCCESS('Seeded departments and time slots.'))

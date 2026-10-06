from django.db import models
from django.core.exceptions import ValidationError




# This pulls in the real teacher accounts your groupmate already built,
# so a schedule entry points at an actual TeacherProfile. Adjust the
# import path below if your project's teacher app isn't literally
# named "teacher".




class Department(models.Model):

    name = models.CharField(max_length=100)
    short_code = models.CharField(max_length=10, unique=True)  # SE, KE, HPC, CT, CFS, BIS...

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.short_code})'

class Major(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE,related_name='majors')
    name = models.CharField(max_length=100)
    short_code = models.CharField(max_length=10, unique=True)
    def __str__(self):
        return f'{self.name}({self.short_code})'

class AcademicClass(models.Model):
    """
    One class group students belong to — e.g. 'Year 1, Semester 1, Section A'
    or 'Year 3, SE, Section A'. This is the same grouping a student record
    would reference, so a schedule built for a class here is exactly what
    that class's students (and their teachers) will see later.
    """


    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, blank=True, null=True,
        help_text='Leave blank for Year 1 & 2. Required from the major years onward.'
    )
    section = models.ForeignKey('admin_dashboard.Section', on_delete=models.CASCADE, related_name='academic_class')
    major = models.ForeignKey(Major, on_delete=models.SET_NULL, blank=True, null=True,related_name='academic_class')
    class Meta:
        unique_together = ('department', 'section')
        ordering = ['department', 'section']

    def __str__(self):
        if self.major:
            return f' {self.section.sem} {self.section.name}'

        return f'Sem {self.section.sem} {self.section}'


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f'{self.code} - {self.name}'


class TimeSlot(models.Model):
    """A fixed period, e.g. 09:00-10:00. Set these up once (Django admin,
    or the seed command below) and every class's timetable reuses them —
    this is what makes the grid line up as a proper timetable."""
    start_time = models.TimeField()
    end_time = models.TimeField()
    label = models.CharField(max_length=30, blank=True)

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        if self.label:
            return self.label
        return f'{self.start_time.strftime("%H:%M")} - {self.end_time.strftime("%H:%M")}'


from django.core.exceptions import ValidationError


class Schedule(models.Model):

    DAY_CHOICES = [
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
    ]

    class_group = models.ForeignKey(
        AcademicClass,
        on_delete=models.CASCADE,
        related_name='schedules'
    )

    day = models.CharField(
        max_length=3,
        choices=DAY_CHOICES
    )

    time_slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.CASCADE
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE
    )

    teacher = models.ForeignKey(
        'admin_dashboard.Teacher',
        on_delete=models.CASCADE,
        related_name='schedules'
    )

    room = models.CharField(
        max_length=30,
        blank=True
    )

    class Meta:
        unique_together = (
            'class_group',
            'day',
            'time_slot',
        )
        ordering = ['day', 'time_slot']

    def clean(self):

        # Teacher မရှိသေးရင် မစစ်ဘူး
        if not self.teacher_id:
            return

        clash = Schedule.objects.filter(
            teacher_id=self.teacher_id,
            day=self.day,
            time_slot_id=self.time_slot_id
        ).exclude(
            pk=self.pk
        )

        if clash.exists():

            teacher_name = (
                self.teacher.name
                if self.teacher_id
                else "This teacher"
            )

            raise ValidationError(
                f'{teacher_name} is already scheduled '
                f'for another class at this day and time.'
            )

    def __str__(self):

        return (
            f'{self.class_group} | '
            f'{self.get_day_display()} '
            f'{self.time_slot} | '
            f'{self.subject.code}'
        )

class Attendance(models.Model):

    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
    ]

    METHOD_CHOICES = [
        ('QR', 'QR Scan'),
        ('MANUAL', 'Teacher Manual'),
    ]

    student = models.ForeignKey('admin_dashboard.Student',on_delete=models.CASCADE,related_name='attendances')

    schedule = models.ForeignKey( Schedule,on_delete=models.CASCADE,related_name='attendances')

    date = models.DateField()

    status = models.CharField(max_length=10,choices=STATUS_CHOICES,default='PRESENT')

    method = models.CharField(max_length=10,choices=METHOD_CHOICES,default='MANUAL' )
    remark = models.CharField(max_length=255,blank=True,null=True )
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'schedule', 'date'],
                name='unique_student_schedule_date'
            )
        ]
        ordering = ['-date']

    def __str__(self):
        return (
            f'{self.student.ID} - '
            f'{self.schedule.subject.code} - '
            f'{self.date} - '
            f'{self.schedule.time_slot} - '
            f'{self.status}'
        )
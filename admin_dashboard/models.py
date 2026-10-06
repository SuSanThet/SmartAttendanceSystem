from django.contrib import admin
from django.core.files.base import ContentFile
from django.db import models
import uuid
import qrcode
from io import BytesIO
from accounts.models import User
from django.core.files import File
from PIL import Image,ImageDraw
from django.conf import settings
from django.core.validators import RegexValidator
from timetable.models import Subject


class Section(models.Model):

    sem = models.CharField(max_length=20)
    name = models.CharField(max_length=30)

    def __str__(self):
        return f"{self.sem} Section-{self.name}"


class Student(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='student')
    ID=models.CharField(max_length=10,primary_key=True, validators=[
        RegexValidator(
            regex=r'^ST\d{3}$',
            message='Student ID must be in the format ST001, ST002, etc.'
        )
    ])
    name=models.CharField(max_length=30)

    section=models.ForeignKey(Section,on_delete=models.CASCADE,related_name='students',null=True,blank=True)
    email=models.EmailField()
    is_active=models.BooleanField(default=True)
    major=models.ForeignKey('timetable.Major',on_delete=models.SET_NULL,null=True,blank=True,related_name='students')
    phone=models.CharField(max_length=30,null=True,blank=True)
    qr_token=models.UUIDField(default=uuid.uuid4,unique=True,editable=False)
    qr_code=models.ImageField(upload_to="student_qr/",null=True,blank=True)
    def __str__(self):
        return f"{self.ID}-{self.name}"

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)


        if not self.qr_code:
            qr = qrcode.make(self.ID)

            buffer = BytesIO()
            qr.save(buffer, format="PNG")

            filename = f"{self.ID}.png"

            self.qr_code.save(
                filename,
                ContentFile(buffer.getvalue()),
                save=False
            )
            super().save(update_fields=["qr_code"])




# Create your models here.

class Teacher(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name='teacher')
    TrID = models.CharField(max_length=10, primary_key=True,validators=[
        RegexValidator(
            regex=r'^Tr\d{3}$',
            message='Teacher ID must be in the format Tr001, Tr002, etc.'
        )
    ])
    name = models.CharField(max_length=30)
    dept = models.ForeignKey(
        'timetable.Department',
        on_delete=models.SET_NULL,
        null=True,blank=True,related_name='teachers')
    position = models.CharField(max_length=30)  # lecture,professor,assistant
    subj = models.ManyToManyField('timetable.Subject',
        blank=True,related_name='teachers')
    email=models.EmailField(blank=True,null=True)
    phone=models.CharField(max_length=30,blank=True,null=True)
    date_join = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )

    @property
    def subjects(self):
        return Subject.objects.filter(
            schedules__teacher=self
        ).distinct()
    def __str__(self):
        return f"{self.TrID}-{self.name}"


class TeachingAssignment(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='assignments', null=True)

    section =models.ForeignKey(Section, on_delete=models.CASCADE, related_name='teaching_assignments', null=True)

    def __str__(self):
        return f"{self.teacher.name}-{self.section}"

class LeaveRequest(models.Model):
    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    )

    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="leave_requests"
    )

    start_date = models.DateField()
    end_date = models.DateField()

    reason = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_leave_requests"
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.requester} - {self.start_date} to {self.end_date}"


class EmailMessage(models.Model):
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_emails"
    )

    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_emails"
    )

    subject = models.CharField(max_length=255)

    message = models.TextField()

    is_read = models.BooleanField(default=False)


    is_deleted_by_sender = models.BooleanField(default=False)

    is_deleted_by_receiver = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replies"
    )

    def __str__(self):
        return f"{self.sender}-{self.subject}"

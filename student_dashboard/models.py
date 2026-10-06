from django.db import models
from admin_dashboard.models import Student
# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
class Profile(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='student_profile',default='')
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)


    def __str__(self):
        if self.student:
            return f"{self.student.name}'s Student Profile"
        return "Student Profile"
from django.db import models
from django.contrib.auth.models import User
from accounts.models import User
from django.conf import settings
from admin_dashboard.models import Teacher

class TeacherProfile(models.Model):
    teacher = models.OneToOneField(
        Teacher,
        on_delete=models.CASCADE,null=True,blank=True,
        related_name="profile"
    )
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        if self.teacher:
            return self.teacher.name
        return "No Teacher"

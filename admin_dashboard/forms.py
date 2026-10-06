
from . models import Student, Section,TeachingAssignment
from accounts.models import User
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin




import re
from django import forms

from admin_dashboard.models import Student


class StudentForm(forms.ModelForm):

    class Meta:
        model = Student

        exclude = [
            "user",
            "qr_token",
            "qr_code",
        ]

    def clean_ID(self):

        student_id = (
            self.cleaned_data.get("ID", "")
            .strip()
            .upper()
        )

        if not re.fullmatch(r"ST\d{3,}", student_id):

            raise forms.ValidationError(
                "Student ID must start with ST and contain numbers. "
                "Example: ST001"
            )

        if Student.objects.filter(
            ID=student_id
        ).exists():

            raise forms.ValidationError(
                "This Student ID already exists."
            )
        if User.objects.filter(account_id=student_id).exists():
            raise forms.ValidationError(
                "This Student ID is already registered."
            )
        return student_id


class StudentSectionForm(forms.ModelForm):

    class Meta:
        model = Student
        fields = ['section']

    section = forms.ModelChoiceField(
        queryset=Section.objects.all(),
        empty_label="Select Section"
    )
from django import forms

from timetable.models import (
    Department,
    Major,
    AcademicClass,
    Subject,

)


class DepartmentForm(forms.ModelForm):

    class Meta:
        model = Department
        fields = ['name', 'short_code']

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Department name'
            }),
            'short_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Short code'
            }),
        }


class MajorForm(forms.ModelForm):

    class Meta:
        model = Major
        fields = ['department', 'name', 'short_code']

        widgets = {
            'department': forms.Select(attrs={
                'class': 'form-select'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Major name'
            }),
            'short_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Short code'
            }),
        }


class SectionForm(forms.ModelForm):

    class Meta:
        model = Section
        fields = ['sem', 'name']

        widgets = {
            'sem': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 1'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. F-101'
            }),
        }


class AcademicClassForm(forms.ModelForm):

    class Meta:
        model = AcademicClass
        fields = ['department', 'section', 'major']

        widgets = {
            'department': forms.Select(attrs={
                'class': 'form-select'
            }),
            'section': forms.Select(attrs={
                'class': 'form-select'
            }),
            'major': forms.Select(attrs={
                'class': 'form-select'
            }),
        }


class TeachingAssignmentForm(forms.ModelForm):

    class Meta:
        model = TeachingAssignment
        fields = ['teacher', 'section']

        widgets = {
            'teacher': forms.Select(attrs={
                'class': 'form-select'
            }),
            'section': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
class SubjectForm(forms.ModelForm):

    class Meta:
        model = Subject
        fields = ['name', 'code', 'department']

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Subject name'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. CS-101'
            }),
            'department': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
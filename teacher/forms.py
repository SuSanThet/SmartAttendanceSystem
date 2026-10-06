import re

from django import forms

from admin_dashboard.models import Teacher
from timetable.models import Subject, Department


class TeacherForm(forms.ModelForm):

    class Meta:
        model = Teacher
        fields = [
            'TrID',
            'name',
            'email',
            'phone',
            'dept',
            'position',
            'subj',

        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['subj'].queryset = Subject.objects.none()

        dept = None

        # Edit
        if self.instance and self.instance.pk:
            dept = self.instance.dept

        # Add / POST
        dept_id = self.data.get('dept')

        if dept_id:
            try:
                dept = Department.objects.get(id=dept_id)
            except Department.DoesNotExist:
                dept = None

        if dept:
            self.fields['subj'].queryset = Subject.objects.filter(
                department=dept
            )
    #validation
    def clean_TrID(self):
        tr_id = self.cleaned_data.get('TrID', '').strip()

        if not re.fullmatch(r'Tr\d{3,}', tr_id):
            raise forms.ValidationError(
                'Teacher ID must start with Tr and contain numbers. '
                'Example: Tr001'
            )

        if Teacher.objects.filter(TrID=tr_id).exclude(
                pk=self.instance.pk
        ).exists():
            raise forms.ValidationError(
                'This Teacher ID already exists.'
            )

        return tr_id
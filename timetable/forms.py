from django import forms

from .models import Schedule
from teacher_dashboard.models import Teacher


class ScheduleForm(forms.ModelForm):

    class Meta:

        model = Schedule

        fields = [
            'class_group',
            'day',
            'time_slot',
            'subject',
            'teacher',
            'room',
        ]

        widgets = {
            'room': forms.TextInput(
                attrs={
                    'placeholder': 'e.g. Room 204 (optional)'
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Teacher DB ထဲက အားလုံးပေါ်မယ်
        self.fields['teacher'].queryset = Teacher.objects.all()

        # Teacher မရွေးဘဲ submit မလုပ်နိုင်
        self.fields['teacher'].required = True


    def clean(self):

        cleaned_data = super().clean()

        class_group = cleaned_data.get('class_group')
        day = cleaned_data.get('day')
        time_slot = cleaned_data.get('time_slot')
        subject = cleaned_data.get('subject')
        teacher = cleaned_data.get('teacher')


        # =====================================
        # 1. Same Class + Day + Time
        # =====================================

        if class_group and day and time_slot:

            qs = Schedule.objects.filter(
                class_group=class_group,
                day=day,
                time_slot=time_slot
            )

            if self.instance.pk:
                qs = qs.exclude(
                    pk=self.instance.pk
                )

            if qs.exists():

                raise forms.ValidationError(
                    'This class already has a subject '
                    'scheduled for this day and time slot.'
                )


        # =====================================
        # 2. Same Teacher + Day + Time
        # =====================================

        if teacher and day and time_slot:

            qs = Schedule.objects.filter(
                teacher_id=teacher.pk,
                day=day,
                time_slot_id=time_slot.pk
            )

            if self.instance.pk:
                qs = qs.exclude(
                    pk=self.instance.pk
                )

            if qs.exists():

                raise forms.ValidationError(
                    f'{teacher.name} already has another '
                    f'class at this day and time slot.'
                )


        # =====================================
        # 3. Teaching Assignment
        # =====================================

        if teacher and class_group:

            section = class_group.section

            assigned = teacher.assignments.filter(
                section=section
            ).exists()

            if not assigned:

                self.add_error(
                    'teacher',
                    f'{teacher.name} is not assigned '
                    f'to this section.'
                )


        # =====================================
        # 4. Teacher + Subject
        # =====================================

        if teacher and subject:

            teaches_subject = teacher.subj.filter(
                pk=subject.pk
            ).exists()

            if not teaches_subject:

                self.add_error(
                    'teacher',
                    f'{teacher.name} is not assigned '
                    f'to teach {subject.code}.'
                )


        return cleaned_data
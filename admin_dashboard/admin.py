from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from admin_dashboard.models import Student, TeachingAssignment, Section, Teacher, LeaveRequest, EmailMessage
from teacher_dashboard.models import TeacherProfile


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('ID', 'name', 'email', 'major', 'is_active')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        # Existing student ဖြစ်ရင် Major နဲ့ Section ကို လုံးဝမပြောင်းနိုင်အောင်လုပ်
        if obj:
            for field_name in ['major', 'section']:
                if field_name in form.base_fields:
                    field = form.base_fields[field_name]

                    # Readonly / disabled
                    field.disabled = True

                    # Related-object buttons အားလုံးဖျောက်
                    widget = field.widget
                    widget.can_add_related = False
                    widget.can_change_related = False
                    widget.can_delete_related = False
                    widget.can_view_related = False

        return form


@admin.register(TeachingAssignment)
class TeachingAssignmentAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'section')


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('sem', 'name')



@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('TrID', 'name', 'dept', 'position', 'email')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        # Existing student ဖြစ်ရင် Major ကို လုံးဝမပြောင်းနိုင်အောင်လုပ်
        if obj and 'dept' in form.base_fields:
            field = form.base_fields['dept']

            # Major ကို readonly/disabled
            field.disabled = True

            # Related-object buttons အားလုံးဖျောက်
            widget = field.widget
            widget.can_add_related = False
            widget.can_change_related = False
            widget.can_delete_related = False
            widget.can_view_related = False

        return form


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('requester', 'start_date', 'end_date')
@admin.register(EmailMessage)
class EmailMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'subject',)

from django.contrib import admin
from .models import Department, AcademicClass, Subject, TimeSlot, Schedule, Major, Attendance


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_code')


@admin.register(AcademicClass)
class AcademicClassAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'major', 'section')
    list_filter = ('major',)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'department')
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        # Existing student ဖြစ်ရင် Major ကို လုံးဝမပြောင်းနိုင်အောင်လုပ်
        if obj and 'department' in form.base_fields:
            field = form.base_fields['department']

            # Major ကို readonly/disabled
            field.disabled = True

            # Related-object buttons အားလုံးဖျောက်
            widget = field.widget
            widget.can_add_related = False
            widget.can_change_related = False
            widget.can_delete_related = False
            widget.can_view_related = False

        return form



@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'start_time', 'end_time')


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('class_group', 'day', 'time_slot', 'subject', 'teacher', 'room')
    list_filter = ('day','class_group__department', 'class_group__section',)

@admin.register(Major)
class MajorAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_code','department')
    list_filter = ('department',)

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):

    list_display = (
        'student',
        'get_subject',
        'get_time_slot',
        'date',
        'status',
        'method',
        'remark',
    )

    list_filter = (
        'status',
        'method',
        'date',
    )

    search_fields = (
        'student__ID',
        'student__name',
        'schedule__subject__code',
        'schedule__subject__name',
    )

    @admin.display(description='Subject')
    def get_subject(self, obj):
        return obj.schedule.subject.code

    @admin.display(description='Time Slot')
    def get_time_slot(self, obj):
        return obj.schedule.time_slot
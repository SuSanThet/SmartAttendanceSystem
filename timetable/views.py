from urllib.parse import urlencode

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse

from teacher_dashboard.models import TeacherProfile
from .models import Schedule, AcademicClass, TimeSlot, Department
from .forms import ScheduleForm

from django.http import JsonResponse
from .models import AcademicClass
from teacher_dashboard.models import TeacherProfile

DAY_LABELS = dict(Schedule.DAY_CHOICES)
DAYS = [code for code, _ in Schedule.DAY_CHOICES]

def get_teachers_for_class(request):
    class_group_id = request.GET.get('class_group')

    if not class_group_id:
        return JsonResponse({'teachers': []})

    try:
        class_group = AcademicClass.objects.get(pk=class_group_id)
    except AcademicClass.DoesNotExist:
        return JsonResponse({'teachers': []})

    section = class_group.section

    teachers = TeacherProfile.objects.filter(
        teacher__assignments__section=section
    ).distinct()

    data = [
        {
            'id': teacher.id,
            'name': str(teacher)
        }
        for teacher in teachers
    ]

    return JsonResponse({'teachers': data})


def schedule_builder(request):
    """
    The visual weekly grid ('draw' the timetable): pick a class, see a
    Mon-Fri x period grid. Click an empty cell to add a subject there,
    click a filled cell to edit or delete it.
    """
    class_groups = AcademicClass.objects.select_related('department').all()
    time_slots = TimeSlot.objects.all()

    selected_class_id = request.GET.get('class_group')
    selected_class = None
    grid = []

    if selected_class_id:
        selected_class = get_object_or_404(AcademicClass, pk=selected_class_id)
        entries = Schedule.objects.filter(class_group=selected_class).select_related(
            'subject', 'teacher', 'time_slot'
        )
        lookup = {(e.day, e.time_slot_id): e for e in entries}

        for slot in time_slots:
            row = {'time_slot': slot, 'cells': []}
            for day_code in DAYS:
                row['cells'].append({
                    'day': day_code,
                    'day_label': DAY_LABELS[day_code],
                    'entry': lookup.get((day_code, slot.id)),
                })
            grid.append(row)

    context = {
        'class_groups': class_groups,
        'selected_class': selected_class,
        'time_slots': time_slots,
        'grid': grid,
    }
    return render(request, 'schedule_builder.html', context)


def schedule_list(request):
    """Filterable table of every schedule entry across every class."""
    schedules = Schedule.objects.select_related(
        'class_group', 'class_group__department', 'subject', 'teacher', 'time_slot'
    )

    sem = request.GET.get('section.sem', '')
    department_id = request.GET.get('department', '')
    day = request.GET.get('day', '')
    TrID = request.GET.get('teacher', '')

    if sem:
        schedules = schedules.filter(class_group__year=sem)
    if department_id:
        schedules = schedules.filter(class_group__department_id=department_id)
    if day:
        schedules = schedules.filter(day=day)
    if TrID:
        schedules = schedules.filter(teacher_id=TrID)

    context = {
        'schedules': schedules,
        'departments': Department.objects.all(),
        'sem': sem,
        'days': Schedule.DAY_CHOICES,
        'teachers': TeacherProfile.objects.all(),
        'filters': {'sem': sem, 'department': department_id, 'day': day, 'teacher': TrID},
    }
    return render(request, 'schedule_list.html', context)


def _back_to_builder(class_group_id):
    url = reverse('schedule_builder')
    if class_group_id:
        url += '?' + urlencode({'class_group': class_group_id})
    return redirect(url)


def schedule_add(request):

    initial = {
        'class_group': request.GET.get('class_group'),
        'day': request.GET.get('day'),
        'time_slot': request.GET.get('time_slot'),
    }

    if request.method == 'POST':

        form = ScheduleForm(request.POST)

        if form.is_valid():

            schedule = form.save()

            messages.success(
                request,
                'Schedule entry added.'
            )

            return _back_to_builder(
                schedule.class_group_id
            )

    else:

        form = ScheduleForm(
            initial=initial
        )

    return render(
        request,
        'schedule_form.html',
        {
            'form': form,
            'mode': 'add'
        }
    )
def schedule_edit(request, pk):
    schedule = get_object_or_404(Schedule, pk=pk)
    if request.method == 'POST':
        form = ScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, 'Schedule entry updated.')
            return _back_to_builder(schedule.class_group_id)
    else:
        form = ScheduleForm(instance=schedule)

    return render(request, 'schedule_form.html', {'form': form, 'mode': 'edit', 'schedule': schedule})


def schedule_delete(request, pk):
    schedule = get_object_or_404(Schedule, pk=pk)
    if request.method == 'POST':
        class_group_id = schedule.class_group_id
        schedule.delete()
        messages.success(request, 'Schedule entry deleted.')
        return _back_to_builder(class_group_id)

    return render(request, 'schedule_confirm_delete.html', {'schedule': schedule})

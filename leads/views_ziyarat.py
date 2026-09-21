"""
Raabta360 — Ziyarat / Activities module (requirements doc, section 9.6)
"""

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .decorators import block_view_only
from .models import (
    ZiyaratActivity, ZiyaratParticipant, Pilgrim, PilgrimGroup, Booking,
    TransportSchedule, ZIYARAT_CITY_CHOICES,
)

_INPUT = {'class': 'form-control'}
_DATE = {'class': 'form-control', 'type': 'date'}
_TIME = {'class': 'form-control', 'type': 'time'}


class ZiyaratActivityForm(forms.ModelForm):
    class Meta:
        model = ZiyaratActivity
        fields = ['name', 'city', 'booking', 'group', 'transport', 'date', 'time',
                  'duration_minutes', 'guide_name', 'guide_phone', 'is_included',
                  'price_per_person', 'notes']
        widgets = {
            'date': forms.DateInput(attrs=_DATE),
            'time': forms.TimeInput(attrs=_TIME),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not isinstance(field.widget, (forms.Textarea, forms.DateInput, forms.TimeInput,
                                              forms.CheckboxInput)):
                field.widget.attrs.setdefault('class', 'form-control')


@login_required
def ziyarat_list(request):
    activities = ZiyaratActivity.objects.select_related('group', 'booking').prefetch_related('participants')

    city = request.GET.get('city')
    if city:
        activities = activities.filter(city=city)

    upcoming = request.GET.get('when')
    today = timezone.localdate()
    if upcoming == 'upcoming':
        activities = activities.filter(date__gte=today)
    elif upcoming == 'past':
        activities = activities.filter(date__lt=today)

    return render(request, 'leads/ziyarat_list.html', {
        'activities': activities,
        'active': 'ziyarat',
        'city_choices': ZIYARAT_CITY_CHOICES,
        'today': today,
    })


@login_required
def ziyarat_detail(request, pk):
    activity = get_object_or_404(ZiyaratActivity, pk=pk)
    assigned_ids = set(activity.participants.values_list('pilgrim_id', flat=True))

    candidates = Pilgrim.objects.all()
    if activity.group_id:
        candidates = candidates.filter(group_id=activity.group_id)

    return render(request, 'leads/ziyarat_detail.html', {
        'activity': activity,
        'participants': activity.participants.select_related('pilgrim'),
        'candidates': candidates,
        'assigned_ids': assigned_ids,
        'active': 'ziyarat',
    })


@login_required
@block_view_only
def ziyarat_create(request):
    if request.method == 'POST':
        form = ZiyaratActivityForm(request.POST)
        if form.is_valid():
            activity = form.save()
            messages.success(request, f'{activity.name} scheduled.')
            return redirect('ziyarat_detail', pk=activity.pk)
    else:
        form = ZiyaratActivityForm(initial={'date': timezone.localdate()})
    return render(request, 'leads/ziyarat_form.html', {
        'form': form, 'active': 'ziyarat', 'title': 'New Ziyarat / Activity',
    })


@login_required
@block_view_only
def ziyarat_edit(request, pk):
    activity = get_object_or_404(ZiyaratActivity, pk=pk)
    if request.method == 'POST':
        form = ZiyaratActivityForm(request.POST, instance=activity)
        if form.is_valid():
            form.save()
            messages.success(request, 'Activity updated.')
            return redirect('ziyarat_detail', pk=activity.pk)
    else:
        form = ZiyaratActivityForm(instance=activity)
    return render(request, 'leads/ziyarat_form.html', {
        'form': form, 'activity': activity, 'active': 'ziyarat',
        'title': f'Edit {activity.name}',
    })


@login_required
@block_view_only
def ziyarat_toggle_participant(request, pk, pilgrim_id):
    """Add/remove a pilgrim from an activity's participant list."""
    activity = get_object_or_404(ZiyaratActivity, pk=pk)
    pilgrim = get_object_or_404(Pilgrim, pk=pilgrim_id)
    existing = ZiyaratParticipant.objects.filter(activity=activity, pilgrim=pilgrim).first()
    if existing:
        existing.delete()
        messages.success(request, f'{pilgrim.full_name} removed from {activity.name}.')
    else:
        ZiyaratParticipant.objects.create(activity=activity, pilgrim=pilgrim)
        messages.success(request, f'{pilgrim.full_name} added to {activity.name}.')
    return redirect('ziyarat_detail', pk=activity.pk)


@login_required
@block_view_only
def ziyarat_mark_attended(request, pk, pilgrim_id):
    participant = get_object_or_404(ZiyaratParticipant, activity_id=pk, pilgrim_id=pilgrim_id)
    participant.attended = not participant.attended
    participant.save(update_fields=['attended'])
    return redirect('ziyarat_detail', pk=pk)

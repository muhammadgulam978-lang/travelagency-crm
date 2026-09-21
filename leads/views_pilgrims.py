"""
Raabta360 — Hajj/Umrah operational modules
Pilgrims, Family/Groups, Document tracking, Profit & Cost, Pipeline Kanban.
"""

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .decorators import block_view_only
from .models import (
    Lead, Booking, Package, Pilgrim, PilgrimGroup, PilgrimDocument, BookingCost,
    LEAD_STATUS_CHOICES, PILGRIM_STATUS_CHOICES, PILGRIM_TRIP_CHOICES,
    PILGRIM_DOC_TYPE_CHOICES, PILGRIM_DOC_STATUS_CHOICES,
)

_INPUT = {'class': 'form-control'}
_DATE = {'class': 'form-control', 'type': 'date'}


# ---------------------------------------------------------------- forms

class PilgrimForm(forms.ModelForm):
    class Meta:
        model = Pilgrim
        fields = [
            'full_name', 'father_husband_name', 'date_of_birth', 'gender',
            'nationality', 'blood_group', 'relationship',
            'cnic', 'passport_number', 'passport_expiry',
            'phone', 'whatsapp', 'email',
            'emergency_contact_name', 'emergency_contact_phone',
            'trip_type', 'status', 'visa_status',
            'group', 'lead', 'booking',
            'room_number', 'flight_number', 'seat_number',
            'travel_history', 'notes',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs=_DATE),
            'passport_expiry': forms.DateInput(attrs=_DATE),
            'travel_history': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not isinstance(field.widget, (forms.Textarea, forms.DateInput)):
                field.widget.attrs.setdefault('class', 'form-control')


class PilgrimGroupForm(forms.ModelForm):
    class Meta:
        model = PilgrimGroup
        fields = ['name', 'trip_type', 'season_year', 'package', 'booking',
                  'lead', 'departure_date', 'return_date', 'notes']
        widgets = {
            'departure_date': forms.DateInput(attrs=_DATE),
            'return_date': forms.DateInput(attrs=_DATE),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not isinstance(field.widget, (forms.Textarea, forms.DateInput)):
                field.widget.attrs.setdefault('class', 'form-control')


class PilgrimDocumentForm(forms.ModelForm):
    class Meta:
        model = PilgrimDocument
        fields = ['document_type', 'status', 'file', 'document_number',
                  'issue_date', 'expiry_date', 'rejection_reason']
        widgets = {
            'issue_date': forms.DateInput(attrs=_DATE),
            'expiry_date': forms.DateInput(attrs=_DATE),
            'rejection_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class BookingCostForm(forms.ModelForm):
    class Meta:
        model = BookingCost
        fields = ['hotel_cost', 'flight_cost', 'visa_cost', 'transport_cost',
                  'food_cost', 'ziyarat_cost', 'guide_cost', 'insurance_cost',
                  'other_cost', 'notes']
        widgets = {'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


# ---------------------------------------------------------------- pilgrims

@login_required
def pilgrim_list(request):
    pilgrims = Pilgrim.objects.select_related('group', 'lead').all()

    q = request.GET.get('q')
    if q:
        pilgrims = pilgrims.filter(
            Q(full_name__icontains=q) | Q(pilgrim_id__icontains=q) |
            Q(passport_number__icontains=q) | Q(cnic__icontains=q) |
            Q(phone__icontains=q)
        )

    status = request.GET.get('status')
    if status:
        pilgrims = pilgrims.filter(status=status)

    trip = request.GET.get('trip')
    if trip:
        pilgrims = pilgrims.filter(trip_type=trip)

    alert = request.GET.get('alert')
    if alert == 'passport':
        cutoff = timezone.localdate() + timezone.timedelta(days=180)
        pilgrims = pilgrims.filter(passport_expiry__lte=cutoff)

    pilgrims = list(pilgrims)
    total = Pilgrim.objects.count()

    context = {
        'pilgrims': pilgrims,
        'active': 'pilgrims',
        'title': 'Pilgrims',
        'total': total,
        'status_choices': PILGRIM_STATUS_CHOICES,
        'trip_choices': PILGRIM_TRIP_CHOICES,
        'expiring_count': sum(1 for p in Pilgrim.objects.all() if p.passport_alert),
    }
    return render(request, 'leads/pilgrim_list.html', context)


@login_required
def pilgrim_detail(request, pk):
    pilgrim = get_object_or_404(Pilgrim, pk=pk)

    existing = {d.document_type: d for d in pilgrim.pilgrim_documents.all()}
    doc_rows = []
    for code, label in PILGRIM_DOC_TYPE_CHOICES:
        doc_rows.append({'code': code, 'label': label, 'doc': existing.get(code)})

    context = {
        'pilgrim': pilgrim,
        'doc_rows': doc_rows,
        'doc_form': PilgrimDocumentForm(),
        'active': 'pilgrims',
    }
    return render(request, 'leads/pilgrim_detail.html', context)


@login_required
@block_view_only
def pilgrim_create(request):
    initial = {}
    lead_id = request.GET.get('lead')
    if lead_id:
        lead = Lead.objects.filter(pk=lead_id).first()
        if lead:
            initial = {
                'full_name': lead.name, 'phone': lead.contact_number,
                'whatsapp': lead.contact_number, 'email': lead.email, 'lead': lead.pk,
            }

    if request.method == 'POST':
        form = PilgrimForm(request.POST)
        if form.is_valid():
            pilgrim = form.save()
            messages.success(request, f'Pilgrim {pilgrim.pilgrim_id} created.')
            return redirect('pilgrim_detail', pk=pilgrim.pk)
    else:
        form = PilgrimForm(initial=initial)

    return render(request, 'leads/pilgrim_form.html', {
        'form': form, 'active': 'pilgrims', 'title': 'New Pilgrim',
    })


@login_required
@block_view_only
def pilgrim_edit(request, pk):
    pilgrim = get_object_or_404(Pilgrim, pk=pk)
    if request.method == 'POST':
        form = PilgrimForm(request.POST, instance=pilgrim)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pilgrim updated.')
            return redirect('pilgrim_detail', pk=pilgrim.pk)
    else:
        form = PilgrimForm(instance=pilgrim)
    return render(request, 'leads/pilgrim_form.html', {
        'form': form, 'pilgrim': pilgrim, 'active': 'pilgrims',
        'title': f'Edit {pilgrim.full_name}',
    })


@login_required
@block_view_only
def pilgrim_document_save(request, pk):
    pilgrim = get_object_or_404(Pilgrim, pk=pk)
    if request.method == 'POST':
        doc_type = request.POST.get('document_type')
        instance = pilgrim.pilgrim_documents.filter(document_type=doc_type).first()
        form = PilgrimDocumentForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.pilgrim = pilgrim
            doc.save()
            messages.success(request, f'{doc.get_document_type_display()} saved.')
        else:
            messages.error(request, 'Could not save the document. Check the fields and try again.')
    return redirect('pilgrim_detail', pk=pilgrim.pk)


@login_required
@block_view_only
def convert_lead_to_pilgrim(request, pk):
    """Lead → Pilgrim conversion (requirements doc section 3)."""
    lead = get_object_or_404(Lead, pk=pk)

    existing = Pilgrim.objects.filter(lead=lead).first()
    if existing:
        messages.info(request, f'This lead already has pilgrim {existing.pilgrim_id}.')
        return redirect('pilgrim_detail', pk=existing.pk)

    trip = 'hajj' if lead.trip_type == 'hajj' else (
        'umrah' if lead.trip_type == 'umrah' else 'tour')

    pilgrim = Pilgrim.objects.create(
        lead=lead,
        full_name=lead.name,
        phone=lead.contact_number or '',
        whatsapp=lead.contact_number or '',
        email=lead.email,
        trip_type=trip,
        relationship='leader',
    )
    lead.status = 'converted'
    lead.save(update_fields=['status', 'updated_at'])

    messages.success(request, f'{lead.name} converted to pilgrim {pilgrim.pilgrim_id}.')
    return redirect('pilgrim_detail', pk=pilgrim.pk)


# ---------------------------------------------------------------- groups

@login_required
def group_list(request):
    groups = PilgrimGroup.objects.prefetch_related('pilgrims').all()

    q = request.GET.get('q')
    if q:
        groups = groups.filter(Q(name__icontains=q) | Q(group_id__icontains=q))

    trip = request.GET.get('trip')
    if trip:
        groups = groups.filter(trip_type=trip)

    return render(request, 'leads/group_list.html', {
        'groups': groups,
        'active': 'groups',
        'title': 'Groups / Families',
        'trip_choices': PILGRIM_TRIP_CHOICES,
    })


@login_required
def group_detail(request, pk):
    group = get_object_or_404(PilgrimGroup, pk=pk)
    pilgrims = group.pilgrims.all()

    rooms = {}
    for p in pilgrims:
        rooms.setdefault(p.room_number or 'Unassigned', []).append(p)

    return render(request, 'leads/group_detail.html', {
        'group': group,
        'pilgrims': pilgrims,
        'rooms': sorted(rooms.items()),
        'active': 'groups',
    })


@login_required
@block_view_only
def group_create(request):
    if request.method == 'POST':
        form = PilgrimGroupForm(request.POST)
        if form.is_valid():
            group = form.save()
            messages.success(request, f'Group {group.group_id} created.')
            return redirect('group_detail', pk=group.pk)
    else:
        form = PilgrimGroupForm()
    return render(request, 'leads/group_form.html', {
        'form': form, 'active': 'groups', 'title': 'New Group / Family',
    })


@login_required
@block_view_only
def group_edit(request, pk):
    group = get_object_or_404(PilgrimGroup, pk=pk)
    if request.method == 'POST':
        form = PilgrimGroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, 'Group updated.')
            return redirect('group_detail', pk=group.pk)
    else:
        form = PilgrimGroupForm(instance=group)
    return render(request, 'leads/group_form.html', {
        'form': form, 'group': group, 'active': 'groups', 'title': f'Edit {group.name}',
    })


# ------------------------------------------------------- profit & cost

@login_required
def profit_report(request):
    """Booking-by-booking cost vs selling price, with margin."""
    bookings = Booking.objects.filter(is_deleted=False).exclude(
        booking_status='cancelled').select_related('cost', 'client', 'company')

    rows = []
    total_selling = total_cost = 0
    for b in bookings:
        cost = getattr(b, 'cost', None)
        selling = float(b.total_amount or 0)
        cost_val = float(cost.total_cost) if cost else 0.0
        profit = selling - cost_val
        rows.append({
            'booking': b,
            'selling': selling,
            'cost': cost_val,
            'profit': profit,
            'margin': round(profit / selling * 100, 1) if selling else 0.0,
            'has_cost': cost is not None,
        })
        total_selling += selling
        total_cost += cost_val

    rows.sort(key=lambda r: -r['profit'])
    total_profit = total_selling - total_cost

    return render(request, 'leads/profit_report.html', {
        'rows': rows,
        'active': 'profit',
        'total_selling': total_selling,
        'total_cost': total_cost,
        'total_profit': total_profit,
        'total_margin': round(total_profit / total_selling * 100, 1) if total_selling else 0.0,
        'missing_costs': sum(1 for r in rows if not r['has_cost']),
    })


@login_required
@block_view_only
def booking_cost_edit(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    cost, _ = BookingCost.objects.get_or_create(booking=booking)

    if request.method == 'POST':
        form = BookingCostForm(request.POST, instance=cost)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cost breakdown saved.')
            return redirect('profit_report')
    else:
        form = BookingCostForm(instance=cost)

    return render(request, 'leads/booking_cost_form.html', {
        'form': form, 'booking': booking, 'cost': cost, 'active': 'profit',
    })


# ---------------------------------------------------------------- kanban

KANBAN_STAGES = ['new', 'contacted', 'qualified', 'positive',
                 'quotation', 'booking_pending', 'converted']


@login_required
def pipeline_kanban(request):
    """Drag-free Kanban board — har stage ka column, cards par AI score."""
    label_map = dict(LEAD_STATUS_CHOICES)
    leads = Lead.objects.select_related('spo').prefetch_related('followups').order_by('-ai_score')

    trip = request.GET.get('trip')
    if trip:
        leads = leads.filter(trip_type=trip)

    spo = request.GET.get('spo')
    if spo:
        leads = leads.filter(spo_id=spo)

    buckets = {code: [] for code in KANBAN_STAGES}
    for lead in leads:
        if lead.status in buckets:
            nxt = None
            for f in lead.followups.all():
                if f.status == 'pending' and (nxt is None or f.follow_up_date < nxt.follow_up_date):
                    nxt = f
            buckets[lead.status].append({
                'lead': lead,
                'next_followup': timezone.localtime(nxt.follow_up_date) if nxt else None,
            })

    columns = [{
        'code': code,
        'label': label_map.get(code, code.title()),
        'cards': buckets[code],
        'count': len(buckets[code]),
    } for code in KANBAN_STAGES]

    from .models import TRIP_TYPE_CHOICES
    from .models import SalesPerson
    return render(request, 'leads/pipeline_kanban.html', {
        'columns': columns,
        'active': 'kanban',
        'status_choices': LEAD_STATUS_CHOICES,
        'trip_types': TRIP_TYPE_CHOICES,
        'spos': SalesPerson.objects.all(),
    })


# ---------------------------------------------------------------- flights (deep-linked to pilgrims)

from .models import BookingFlight, BookingFlightPassenger, FLIGHT_LEG_CHOICES, BOOKING_FLIGHT_STATUS_CHOICES, TransportSchedule  # noqa: E402


class BookingFlightForm(forms.ModelForm):
    class Meta:
        model = BookingFlight
        fields = ['booking', 'group', 'leg', 'airline', 'flight_no', 'pnr', 'origin',
                  'destination', 'departure_date', 'departure_time', 'arrival_date',
                  'arrival_time', 'status', 'ticket_amount', 'notes']
        widgets = {
            'departure_date': forms.DateInput(attrs=_DATE),
            'arrival_date': forms.DateInput(attrs=_DATE),
            'departure_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'arrival_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not isinstance(field.widget, (forms.Textarea, forms.DateInput, forms.TimeInput)):
                field.widget.attrs.setdefault('class', 'form-control')


@login_required
def flight_list(request):
    flights = BookingFlight.objects.select_related('booking', 'group').prefetch_related('passengers')

    leg = request.GET.get('leg')
    if leg:
        flights = flights.filter(leg=leg)
    status = request.GET.get('status')
    if status:
        flights = flights.filter(status=status)

    return render(request, 'leads/flight_list.html', {
        'flights': flights,
        'active': 'flights',
        'leg_choices': FLIGHT_LEG_CHOICES,
        'status_choices': BOOKING_FLIGHT_STATUS_CHOICES,
    })


@login_required
def flight_detail(request, pk):
    flight = get_object_or_404(BookingFlight, pk=pk)
    assigned_ids = set(flight.passengers.values_list('pilgrim_id', flat=True))
    candidates = Pilgrim.objects.all()
    if flight.group_id:
        candidates = candidates.filter(group_id=flight.group_id)
    elif flight.booking_id:
        candidates = candidates.filter(booking_id=flight.booking_id)

    return render(request, 'leads/flight_detail.html', {
        'flight': flight,
        'passengers': flight.passengers.select_related('pilgrim'),
        'candidates': candidates,
        'assigned_ids': assigned_ids,
        'active': 'flights',
    })


@login_required
@block_view_only
def flight_create(request):
    if request.method == 'POST':
        form = BookingFlightForm(request.POST)
        if form.is_valid():
            flight = form.save()
            messages.success(request, f'{flight.get_leg_display()} flight {flight.flight_no or ""} scheduled.')
            return redirect('flight_detail', pk=flight.pk)
    else:
        form = BookingFlightForm()
    return render(request, 'leads/flight_form.html', {
        'form': form, 'active': 'flights', 'title': 'New Flight',
    })


@login_required
@block_view_only
def flight_edit(request, pk):
    flight = get_object_or_404(BookingFlight, pk=pk)
    if request.method == 'POST':
        form = BookingFlightForm(request.POST, instance=flight)
        if form.is_valid():
            form.save()
            messages.success(request, 'Flight updated.')
            return redirect('flight_detail', pk=flight.pk)
    else:
        form = BookingFlightForm(instance=flight)
    return render(request, 'leads/flight_form.html', {
        'form': form, 'flight': flight, 'active': 'flights',
        'title': f'Edit {flight.flight_no or "flight"}',
    })


@login_required
@block_view_only
def flight_assign_passenger(request, pk):
    """Assign a pilgrim (with seat/baggage/ticket) to a flight leg."""
    flight = get_object_or_404(BookingFlight, pk=pk)
    if request.method == 'POST':
        pilgrim_id = request.POST.get('pilgrim')
        pilgrim = get_object_or_404(Pilgrim, pk=pilgrim_id)
        obj, created = BookingFlightPassenger.objects.get_or_create(
            flight=flight, pilgrim=pilgrim,
            defaults={
                'seat_number': request.POST.get('seat_number', ''),
                'baggage': request.POST.get('baggage', ''),
                'ticket_number': request.POST.get('ticket_number', ''),
            }
        )
        if not created:
            obj.seat_number = request.POST.get('seat_number', obj.seat_number)
            obj.baggage = request.POST.get('baggage', obj.baggage)
            obj.ticket_number = request.POST.get('ticket_number', obj.ticket_number)
            obj.save()
        messages.success(request, f'{pilgrim.full_name} assigned to this flight.')
    return redirect('flight_detail', pk=flight.pk)


@login_required
@block_view_only
def flight_remove_passenger(request, pk, pilgrim_id):
    BookingFlightPassenger.objects.filter(flight_id=pk, pilgrim_id=pilgrim_id).delete()
    return redirect('flight_detail', pk=pk)


# ---------------------------------------------------------------- transport (deep-linked to pilgrims/groups)

class TransportScheduleForm(forms.ModelForm):
    class Meta:
        model = TransportSchedule
        fields = ['booking', 'group', 'transfer_type', 'vehicle', 'driver_name', 'driver_phone',
                  'pickup_location', 'dropoff_location', 'scheduled_at', 'status', 'cost', 'notes']
        widgets = {
            'scheduled_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not isinstance(field.widget, (forms.Textarea, forms.DateTimeInput)):
                field.widget.attrs.setdefault('class', 'form-control')


@login_required
def transport_list(request):
    schedules = TransportSchedule.objects.select_related('booking', 'group', 'vehicle').prefetch_related('pilgrims')
    status = request.GET.get('status')
    if status:
        schedules = schedules.filter(status=status)
    return render(request, 'leads/transport_list.html', {
        'schedules': schedules, 'active': 'transport',
    })


@login_required
def transport_detail(request, pk):
    schedule = get_object_or_404(TransportSchedule, pk=pk)
    assigned_ids = set(schedule.pilgrims.values_list('pk', flat=True))
    candidates = Pilgrim.objects.all()
    if schedule.group_id:
        candidates = candidates.filter(group_id=schedule.group_id)
    elif schedule.booking_id:
        candidates = candidates.filter(booking_id=schedule.booking_id)

    return render(request, 'leads/transport_detail.html', {
        'schedule': schedule,
        'assigned_pilgrims': schedule.pilgrims.all(),
        'candidates': candidates,
        'assigned_ids': assigned_ids,
        'active': 'transport',
    })


@login_required
@block_view_only
def transport_create(request):
    if request.method == 'POST':
        form = TransportScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save()
            messages.success(request, 'Transport schedule created.')
            return redirect('transport_detail', pk=schedule.pk)
    else:
        form = TransportScheduleForm()
    return render(request, 'leads/transport_form.html', {
        'form': form, 'active': 'transport', 'title': 'New Transport Schedule',
    })


@login_required
@block_view_only
def transport_edit(request, pk):
    schedule = get_object_or_404(TransportSchedule, pk=pk)
    if request.method == 'POST':
        form = TransportScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transport schedule updated.')
            return redirect('transport_detail', pk=schedule.pk)
    else:
        form = TransportScheduleForm(instance=schedule)
    return render(request, 'leads/transport_form.html', {
        'form': form, 'schedule': schedule, 'active': 'transport',
        'title': 'Edit Transport Schedule',
    })


@login_required
@block_view_only
def transport_toggle_pilgrim(request, pk, pilgrim_id):
    schedule = get_object_or_404(TransportSchedule, pk=pk)
    pilgrim = get_object_or_404(Pilgrim, pk=pilgrim_id)
    if schedule.pilgrims.filter(pk=pilgrim.pk).exists():
        schedule.pilgrims.remove(pilgrim)
        messages.success(request, f'{pilgrim.full_name} removed from this transfer.')
    else:
        schedule.pilgrims.add(pilgrim)
        messages.success(request, f'{pilgrim.full_name} assigned to this transfer.')
    return redirect('transport_detail', pk=schedule.pk)

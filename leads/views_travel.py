"""
Travel-agency specific CRUD views:
Hotels, Suppliers, Transportation, Itineraries, Corporate Travel
Requests, Bulk Email Campaigns and Reviews.

Kept in a separate module from views.py (which already covers
leads/quotations/bookings/packages/visa) to keep this feature set
easy to locate and maintain.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q

from .models import (
    Hotel, HotelReservation, HOTEL_STAR_CHOICES, MEAL_PLAN_CHOICES,
    Supplier, SUPPLIER_TYPE_CHOICES,
    Vehicle, VEHICLE_TYPE_CHOICES, TransportSchedule,
    TRANSFER_TYPE_CHOICES, TRANSPORT_STATUS_CHOICES,
    Itinerary, ItineraryDay, TOUR_TYPE_CHOICES,
    CorporateTravelRequest, TRAVEL_REQUEST_STATUS_CHOICES,
    BulkEmailCampaign, BulkEmailRecipient,
    Review,
    Company, Contact, Lead, Booking, Package,
)


# ═══════════════════════ HOTELS ═══════════════════════

@login_required
def hotel_list(request):
    hotels = Hotel.objects.all()
    q = request.GET.get('q')
    if q:
        hotels = hotels.filter(Q(name__icontains=q) | Q(city__icontains=q))
    return render(request, 'leads/hotel_list.html', {
        'hotels': hotels, 'active': 'hotels', 'title': 'Hotels',
    })


@login_required
def hotel_create(request):
    if request.method == 'POST':
        Hotel.objects.create(
            name=request.POST.get('name'),
            city=request.POST.get('city'),
            country=request.POST.get('country', ''),
            star_rating=request.POST.get('star_rating', '3'),
            address=request.POST.get('address', ''),
            contact_person=request.POST.get('contact_person', ''),
            phone=request.POST.get('phone', ''),
            email=request.POST.get('email', ''),
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, 'Hotel added.')
        return redirect('hotel_list')
    return render(request, 'leads/hotel_form.html', {
        'active': 'hotels', 'title': 'Add Hotel', 'star_choices': HOTEL_STAR_CHOICES,
    })


@login_required
def hotel_edit(request, pk):
    hotel = get_object_or_404(Hotel, pk=pk)
    if request.method == 'POST':
        hotel.name = request.POST.get('name')
        hotel.city = request.POST.get('city')
        hotel.country = request.POST.get('country', '')
        hotel.star_rating = request.POST.get('star_rating', '3')
        hotel.address = request.POST.get('address', '')
        hotel.contact_person = request.POST.get('contact_person', '')
        hotel.phone = request.POST.get('phone', '')
        hotel.email = request.POST.get('email', '')
        hotel.notes = request.POST.get('notes', '')
        hotel.save()
        messages.success(request, 'Hotel updated.')
        return redirect('hotel_list')
    return render(request, 'leads/hotel_form.html', {
        'active': 'hotels', 'title': 'Edit Hotel', 'hotel': hotel, 'star_choices': HOTEL_STAR_CHOICES,
    })


@login_required
def hotel_delete(request, pk):
    hotel = get_object_or_404(Hotel, pk=pk)
    hotel.delete()
    messages.success(request, 'Hotel deleted.')
    return redirect('hotel_list')


@login_required
def hotel_reservation_list(request):
    reservations = HotelReservation.objects.select_related('hotel', 'booking', 'lead').all()
    status = request.GET.get('status')
    if status:
        reservations = reservations.filter(status=status)
    return render(request, 'leads/hotel_reservation_list.html', {
        'reservations': reservations, 'active': 'hotels', 'title': 'Hotel Reservations',
    })


@login_required
def hotel_reservation_create(request):
    if request.method == 'POST':
        HotelReservation.objects.create(
            hotel_id=request.POST.get('hotel') or None,
            lead_id=request.POST.get('lead') or None,
            room_type=request.POST.get('room_type', ''),
            meal_plan=request.POST.get('meal_plan', 'bb'),
            check_in=request.POST.get('check_in') or None,
            check_out=request.POST.get('check_out') or None,
            nights=request.POST.get('nights') or 1,
            rooms=request.POST.get('rooms') or 1,
            rate_per_night=request.POST.get('rate_per_night') or 0,
            confirmation_number=request.POST.get('confirmation_number', ''),
            cancellation_policy=request.POST.get('cancellation_policy', ''),
            status=request.POST.get('status', 'draft'),
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, 'Hotel reservation created.')
        return redirect('hotel_reservation_list')
    return render(request, 'leads/hotel_reservation_form.html', {
        'active': 'hotels', 'title': 'New Hotel Reservation',
        'hotels': Hotel.objects.filter(is_active=True), 'leads': Lead.objects.all(),
        'meal_plans': MEAL_PLAN_CHOICES,
    })


@login_required
def hotel_reservation_edit(request, pk):
    res = get_object_or_404(HotelReservation, pk=pk)
    if request.method == 'POST':
        res.hotel_id = request.POST.get('hotel') or None
        res.lead_id = request.POST.get('lead') or None
        res.room_type = request.POST.get('room_type', '')
        res.meal_plan = request.POST.get('meal_plan', 'bb')
        res.check_in = request.POST.get('check_in') or None
        res.check_out = request.POST.get('check_out') or None
        res.nights = request.POST.get('nights') or 1
        res.rooms = request.POST.get('rooms') or 1
        res.rate_per_night = request.POST.get('rate_per_night') or 0
        res.confirmation_number = request.POST.get('confirmation_number', '')
        res.cancellation_policy = request.POST.get('cancellation_policy', '')
        res.status = request.POST.get('status', 'draft')
        res.notes = request.POST.get('notes', '')
        res.save()
        messages.success(request, 'Hotel reservation updated.')
        return redirect('hotel_reservation_list')
    return render(request, 'leads/hotel_reservation_form.html', {
        'active': 'hotels', 'title': 'Edit Hotel Reservation', 'res': res,
        'hotels': Hotel.objects.filter(is_active=True), 'leads': Lead.objects.all(),
        'meal_plans': MEAL_PLAN_CHOICES,
    })


@login_required
def hotel_reservation_delete(request, pk):
    res = get_object_or_404(HotelReservation, pk=pk)
    res.delete()
    messages.success(request, 'Reservation deleted.')
    return redirect('hotel_reservation_list')


# ═══════════════════════ SUPPLIERS ═══════════════════════

@login_required
def supplier_list(request):
    suppliers = Supplier.objects.all()
    supplier_type = request.GET.get('type')
    if supplier_type:
        suppliers = suppliers.filter(supplier_type=supplier_type)
    return render(request, 'leads/supplier_list.html', {
        'suppliers': suppliers, 'active': 'suppliers', 'title': 'Suppliers',
        'type_choices': SUPPLIER_TYPE_CHOICES,
    })


@login_required
def supplier_create(request):
    if request.method == 'POST':
        Supplier.objects.create(
            name=request.POST.get('name'),
            supplier_type=request.POST.get('supplier_type', 'other'),
            contact_person=request.POST.get('contact_person', ''),
            phone=request.POST.get('phone', ''),
            email=request.POST.get('email', ''),
            city=request.POST.get('city', ''),
            country=request.POST.get('country', ''),
            rates_notes=request.POST.get('rates_notes', ''),
        )
        messages.success(request, 'Supplier added.')
        return redirect('supplier_list')
    return render(request, 'leads/supplier_form.html', {
        'active': 'suppliers', 'title': 'Add Supplier', 'type_choices': SUPPLIER_TYPE_CHOICES,
    })


@login_required
def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.name = request.POST.get('name')
        supplier.supplier_type = request.POST.get('supplier_type', 'other')
        supplier.contact_person = request.POST.get('contact_person', '')
        supplier.phone = request.POST.get('phone', '')
        supplier.email = request.POST.get('email', '')
        supplier.city = request.POST.get('city', '')
        supplier.country = request.POST.get('country', '')
        supplier.rates_notes = request.POST.get('rates_notes', '')
        supplier.save()
        messages.success(request, 'Supplier updated.')
        return redirect('supplier_list')
    return render(request, 'leads/supplier_form.html', {
        'active': 'suppliers', 'title': 'Edit Supplier', 'supplier': supplier,
        'type_choices': SUPPLIER_TYPE_CHOICES,
    })


@login_required
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    supplier.delete()
    messages.success(request, 'Supplier deleted.')
    return redirect('supplier_list')


# ═══════════════════════ TRANSPORTATION ═══════════════════════

@login_required
def transport_list(request):
    schedules = TransportSchedule.objects.select_related('vehicle', 'booking', 'lead').all()
    status = request.GET.get('status')
    if status:
        schedules = schedules.filter(status=status)
    return render(request, 'leads/transport_list.html', {
        'schedules': schedules, 'active': 'transportation', 'title': 'Transportation',
    })


@login_required
def transport_create(request):
    if request.method == 'POST':
        TransportSchedule.objects.create(
            lead_id=request.POST.get('lead') or None,
            transfer_type=request.POST.get('transfer_type', 'airport_pickup'),
            vehicle_id=request.POST.get('vehicle') or None,
            driver_name=request.POST.get('driver_name', ''),
            driver_phone=request.POST.get('driver_phone', ''),
            pickup_location=request.POST.get('pickup_location', ''),
            dropoff_location=request.POST.get('dropoff_location', ''),
            scheduled_at=request.POST.get('scheduled_at') or None,
            status=request.POST.get('status', 'scheduled'),
            cost=request.POST.get('cost') or 0,
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, 'Transport scheduled.')
        return redirect('transport_list')
    return render(request, 'leads/transport_form.html', {
        'active': 'transportation', 'title': 'Schedule Transport',
        'leads': Lead.objects.all(), 'vehicles': Vehicle.objects.filter(is_active=True),
        'transfer_types': TRANSFER_TYPE_CHOICES, 'status_choices': TRANSPORT_STATUS_CHOICES,
    })


@login_required
def transport_edit(request, pk):
    sched = get_object_or_404(TransportSchedule, pk=pk)
    if request.method == 'POST':
        sched.lead_id = request.POST.get('lead') or None
        sched.transfer_type = request.POST.get('transfer_type', 'airport_pickup')
        sched.vehicle_id = request.POST.get('vehicle') or None
        sched.driver_name = request.POST.get('driver_name', '')
        sched.driver_phone = request.POST.get('driver_phone', '')
        sched.pickup_location = request.POST.get('pickup_location', '')
        sched.dropoff_location = request.POST.get('dropoff_location', '')
        sched.scheduled_at = request.POST.get('scheduled_at') or None
        sched.status = request.POST.get('status', 'scheduled')
        sched.cost = request.POST.get('cost') or 0
        sched.notes = request.POST.get('notes', '')
        sched.save()
        messages.success(request, 'Transport schedule updated.')
        return redirect('transport_list')
    return render(request, 'leads/transport_form.html', {
        'active': 'transportation', 'title': 'Edit Transport', 'sched': sched,
        'leads': Lead.objects.all(), 'vehicles': Vehicle.objects.filter(is_active=True),
        'transfer_types': TRANSFER_TYPE_CHOICES, 'status_choices': TRANSPORT_STATUS_CHOICES,
    })


@login_required
def transport_delete(request, pk):
    sched = get_object_or_404(TransportSchedule, pk=pk)
    sched.delete()
    messages.success(request, 'Transport schedule deleted.')
    return redirect('transport_list')


@login_required
def vehicle_list(request):
    vehicles = Vehicle.objects.select_related('supplier').all()
    return render(request, 'leads/vehicle_list.html', {
        'vehicles': vehicles, 'active': 'transportation', 'title': 'Vehicles',
    })


@login_required
def vehicle_create(request):
    if request.method == 'POST':
        Vehicle.objects.create(
            vehicle_type=request.POST.get('vehicle_type', 'sedan'),
            make_model=request.POST.get('make_model', ''),
            plate_number=request.POST.get('plate_number', ''),
            capacity=request.POST.get('capacity') or 4,
            supplier_id=request.POST.get('supplier') or None,
        )
        messages.success(request, 'Vehicle added.')
        return redirect('vehicle_list')
    return render(request, 'leads/vehicle_form.html', {
        'active': 'transportation', 'title': 'Add Vehicle',
        'vehicle_types': VEHICLE_TYPE_CHOICES, 'suppliers': Supplier.objects.filter(is_active=True),
    })


@login_required
def vehicle_delete(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    vehicle.delete()
    messages.success(request, 'Vehicle removed.')
    return redirect('vehicle_list')


# ═══════════════════════ ITINERARIES ═══════════════════════

@login_required
def itinerary_list(request):
    itineraries = Itinerary.objects.select_related('lead', 'booking', 'package').all()
    tour_type = request.GET.get('type')
    if tour_type:
        itineraries = itineraries.filter(tour_type=tour_type)
    return render(request, 'leads/itinerary_list.html', {
        'itineraries': itineraries, 'active': 'itineraries', 'title': 'Tours & Itineraries',
        'tour_types': TOUR_TYPE_CHOICES,
    })


@login_required
def itinerary_create(request):
    if request.method == 'POST':
        itinerary = Itinerary.objects.create(
            title=request.POST.get('title'),
            tour_type=request.POST.get('tour_type', 'group'),
            lead_id=request.POST.get('lead') or None,
            destination=request.POST.get('destination', ''),
            start_date=request.POST.get('start_date') or None,
            end_date=request.POST.get('end_date') or None,
            notes=request.POST.get('notes', ''),
            created_by=request.user,
        )
        messages.success(request, 'Itinerary created. Add day-by-day details next.')
        return redirect('itinerary_detail', pk=itinerary.pk)
    return render(request, 'leads/itinerary_form.html', {
        'active': 'itineraries', 'title': 'New Itinerary',
        'tour_types': TOUR_TYPE_CHOICES, 'leads': Lead.objects.all(),
    })


@login_required
def itinerary_detail(request, pk):
    itinerary = get_object_or_404(Itinerary, pk=pk)
    return render(request, 'leads/itinerary_detail.html', {
        'itinerary': itinerary, 'active': 'itineraries', 'title': itinerary.title,
        'days': itinerary.days.all(),
    })


@login_required
def itinerary_edit(request, pk):
    itinerary = get_object_or_404(Itinerary, pk=pk)
    if request.method == 'POST':
        itinerary.title = request.POST.get('title')
        itinerary.tour_type = request.POST.get('tour_type', 'group')
        itinerary.lead_id = request.POST.get('lead') or None
        itinerary.destination = request.POST.get('destination', '')
        itinerary.start_date = request.POST.get('start_date') or None
        itinerary.end_date = request.POST.get('end_date') or None
        itinerary.notes = request.POST.get('notes', '')
        itinerary.save()
        messages.success(request, 'Itinerary updated.')
        return redirect('itinerary_detail', pk=pk)
    return render(request, 'leads/itinerary_form.html', {
        'active': 'itineraries', 'title': 'Edit Itinerary', 'itinerary': itinerary,
        'tour_types': TOUR_TYPE_CHOICES, 'leads': Lead.objects.all(),
    })


@login_required
def itinerary_delete(request, pk):
    itinerary = get_object_or_404(Itinerary, pk=pk)
    itinerary.delete()
    messages.success(request, 'Itinerary deleted.')
    return redirect('itinerary_list')


@login_required
def itinerary_day_add(request, itinerary_pk):
    itinerary = get_object_or_404(Itinerary, pk=itinerary_pk)
    if request.method == 'POST':
        next_day = (itinerary.days.count() or 0) + 1
        ItineraryDay.objects.create(
            itinerary=itinerary,
            day_number=request.POST.get('day_number') or next_day,
            date=request.POST.get('date') or None,
            title=request.POST.get('title', ''),
            activities=request.POST.get('activities', ''),
            meals=request.POST.get('meals', ''),
            hotel_detail=request.POST.get('hotel_detail', ''),
            flight_detail=request.POST.get('flight_detail', ''),
            instructions=request.POST.get('instructions', ''),
        )
        messages.success(request, f'Day {next_day} added.')
    return redirect('itinerary_detail', pk=itinerary_pk)


@login_required
def itinerary_day_delete(request, pk):
    day = get_object_or_404(ItineraryDay, pk=pk)
    itinerary_pk = day.itinerary_id
    day.delete()
    messages.success(request, 'Day removed.')
    return redirect('itinerary_detail', pk=itinerary_pk)


# ═══════════════════════ CORPORATE TRAVEL ═══════════════════════

@login_required
def corporate_request_list(request):
    requests_qs = CorporateTravelRequest.objects.select_related('company', 'employee').all()
    status = request.GET.get('status')
    if status:
        requests_qs = requests_qs.filter(status=status)
    return render(request, 'leads/corporate_request_list.html', {
        'requests': requests_qs, 'active': 'corporate', 'title': 'Corporate Travel Requests',
        'status_choices': TRAVEL_REQUEST_STATUS_CHOICES,
    })


@login_required
def corporate_request_create(request):
    if request.method == 'POST':
        CorporateTravelRequest.objects.create(
            company_id=request.POST.get('company'),
            employee_id=request.POST.get('employee') or None,
            purpose=request.POST.get('purpose', ''),
            destination=request.POST.get('destination', ''),
            travel_date=request.POST.get('travel_date') or None,
            return_date=request.POST.get('return_date') or None,
            estimated_cost=request.POST.get('estimated_cost') or 0,
            corporate_rate_applied=bool(request.POST.get('corporate_rate_applied')),
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, 'Corporate travel request created.')
        return redirect('corporate_request_list')
    return render(request, 'leads/corporate_request_form.html', {
        'active': 'corporate', 'title': 'New Corporate Travel Request',
        'companies': Company.objects.all(), 'contacts': Contact.objects.all(),
    })


@login_required
def corporate_request_status(request, pk, status):
    req = get_object_or_404(CorporateTravelRequest, pk=pk)
    valid = dict(TRAVEL_REQUEST_STATUS_CHOICES)
    if status in valid:
        req.status = status
        if status == 'approved':
            req.approved_by = request.user
        req.save()
        messages.success(request, f'Request marked as {valid[status]}.')
    return redirect('corporate_request_list')


@login_required
def corporate_request_delete(request, pk):
    req = get_object_or_404(CorporateTravelRequest, pk=pk)
    req.delete()
    messages.success(request, 'Request deleted.')
    return redirect('corporate_request_list')


# ═══════════════════════ BULK EMAIL ═══════════════════════

@login_required
def bulk_email_list(request):
    campaigns = BulkEmailCampaign.objects.select_related('created_by').all()
    return render(request, 'leads/bulk_email_list.html', {
        'campaigns': campaigns, 'active': 'bulk_email', 'title': 'Bulk Email Campaigns',
    })


def _segment_leads(destination='', trip_type='', lead_status='', country=''):
    leads = Lead.objects.exclude(email__isnull=True).exclude(email__exact='')
    if destination:
        leads = leads.filter(destination__icontains=destination)
    if trip_type:
        leads = leads.filter(trip_type=trip_type)
    if lead_status:
        leads = leads.filter(status=lead_status)
    if country:
        leads = leads.filter(country__icontains=country)
    return leads


@login_required
def bulk_email_create(request):
    if request.method == 'POST':
        destination = request.POST.get('filter_destination', '')
        trip_type = request.POST.get('filter_trip_type', '')
        lead_status = request.POST.get('filter_lead_status', '')
        country = request.POST.get('filter_country', '')
        leads = _segment_leads(destination, trip_type, lead_status, country)

        campaign = BulkEmailCampaign.objects.create(
            name=request.POST.get('name'),
            subject=request.POST.get('subject'),
            body=request.POST.get('body'),
            filter_destination=destination,
            filter_trip_type=trip_type,
            filter_lead_status=lead_status,
            filter_country=country,
            recipient_count=leads.count(),
            created_by=request.user,
        )
        for lead in leads:
            BulkEmailRecipient.objects.create(campaign=campaign, lead=lead, email=lead.email)
        messages.success(
            request,
            f'Campaign "{campaign.name}" created as draft with {campaign.recipient_count} recipients. Review and send it.'
        )
        return redirect('bulk_email_detail', pk=campaign.pk)

    return render(request, 'leads/bulk_email_form.html', {
        'active': 'bulk_email', 'title': 'New Bulk Email Campaign',
    })


@login_required
def bulk_email_detail(request, pk):
    campaign = get_object_or_404(BulkEmailCampaign, pk=pk)
    return render(request, 'leads/bulk_email_detail.html', {
        'campaign': campaign, 'active': 'bulk_email', 'title': campaign.name,
        'recipients': campaign.recipients.all()[:200],
    })


@login_required
def bulk_email_send(request, pk):
    """Send in a controlled batch through the configured email backend."""
    campaign = get_object_or_404(BulkEmailCampaign, pk=pk)
    if campaign.status == 'sent':
        messages.info(request, 'This campaign was already sent.')
        return redirect('bulk_email_detail', pk=pk)

    campaign.status = 'sending'
    campaign.save(update_fields=['status'])

    sent, failed = 0, 0
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None)
    for recipient in campaign.recipients.filter(status='pending'):
        try:
            send_mail(
                campaign.subject, campaign.body, from_email,
                [recipient.email], fail_silently=False,
            )
            recipient.status = 'sent'
            sent += 1
        except Exception:
            recipient.status = 'failed'
            failed += 1
        from django.utils import timezone
        recipient.sent_at = timezone.now()
        recipient.save(update_fields=['status', 'sent_at'])

    from django.utils import timezone
    campaign.sent_count = sent
    campaign.failed_count = failed
    campaign.status = 'sent' if failed == 0 else ('failed' if sent == 0 else 'sent')
    campaign.sent_at = timezone.now()
    campaign.save(update_fields=['sent_count', 'failed_count', 'status', 'sent_at'])

    messages.success(request, f'Campaign sent: {sent} delivered, {failed} failed.')
    return redirect('bulk_email_detail', pk=pk)


@login_required
def bulk_email_delete(request, pk):
    campaign = get_object_or_404(BulkEmailCampaign, pk=pk)
    campaign.delete()
    messages.success(request, 'Campaign deleted.')
    return redirect('bulk_email_list')


# ═══════════════════════ REVIEWS ═══════════════════════

@login_required
def review_list(request):
    reviews = Review.objects.select_related('lead', 'booking').all()
    return render(request, 'leads/review_list.html', {
        'reviews': reviews, 'active': 'reviews', 'title': 'Reviews & Feedback',
    })


@login_required
def review_create(request):
    if request.method == 'POST':
        Review.objects.create(
            lead_id=request.POST.get('lead') or None,
            booking_id=request.POST.get('booking') or None,
            rating=request.POST.get('rating') or 5,
            comment=request.POST.get('comment', ''),
            is_public=bool(request.POST.get('is_public')),
        )
        messages.success(request, 'Review recorded.')
        return redirect('review_list')
    return render(request, 'leads/review_form.html', {
        'active': 'reviews', 'title': 'Add Review',
        'leads': Lead.objects.all(), 'bookings': Booking.objects.all(),
    })


@login_required
def review_delete(request, pk):
    review = get_object_or_404(Review, pk=pk)
    review.delete()
    messages.success(request, 'Review deleted.')
    return redirect('review_list')

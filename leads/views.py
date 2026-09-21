from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from .forms import LeadForm, FollowUpForm, PaymentForm, ScheduledPaymentForm, InstallmentForm
from django.contrib.auth.models import User
from .decorators import role_required
from django.db.models import Sum, Count
import csv
import io
import json
import calendar
import openpyxl
from .ai_assignment import assign_lead_with_ai
from .duplicate_detector import check_and_mark_duplicate
from .ai_scorer import update_lead_score
from .ai_next_action import get_next_action
from .ai_closing import update_closing_probability
from .ai_followup_messages import generate_followup_message
from .ai_meeting_summary import save_meeting_summary
from .ai_forecasting import generate_sales_forecast
from .ai_churn import update_churn_risk, get_high_churn_leads
from .ai_upsell import get_upsell_recommendations
from .ai_ltv import update_lifetime_value
from .ai_forecasting import generate_sales_forecast
from .ai_churn import get_high_churn_leads
from django.views.decorators.http import require_POST
from .decorators import role_required, block_view_only
from django.db.models import Q
from django.contrib.auth.models import User
from .ai_proposal_writer import extract_pdf_text, generate_proposal
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from leads.assistant.service import AssistantService
from leads.models import AssistantPermission, AssistantConversation
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from .models import EmailLog
import json
import requests
from datetime import timedelta, datetime
from decimal import Decimal, InvalidOperation

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET

from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Dial

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from .models import Lead, CallLog, CallSchedule, GoogleCredential
from django.core.paginator import Paginator


from .models import (Lead, FollowUp, SalesPerson, Payment,
                     ScheduledPayment, Installment, UserProfile,
                     Company, Contact, Opportunity,
                     Quotation, QuotationItem,
                     Meeting, GeneralTask, CommunicationLog,
                      ActivityLog, Document,
                     Contract, Notification, Proposal,
                     Booking, BookingPerson, BookingTicket, BookingHotel, BookingRoute, BookingVisa,
                     Package, PackageAccommodation, PackageTransport, PackageFlight, PackageTrain,
                     VisaApplication, VisaDocumentChecklistItem,
                     VISA_APPLICATION_STATUS_CHOICES, VISA_CATEGORY_CHOICES, VISA_DOC_STATUS_CHOICES,
                     MEDINA_ARRIVAL_CHOICES, HAJJ_DURATION_CHOICES, HIJRI_MONTH_CHOICES,
                     PACKAGE_ROOM_SHARING_CHOICES, PACKAGE_PLACE_CHOICES, PACKAGE_ACCOMMODATION_TYPE_CHOICES,
                     SAUDI_STAR_RATING_CHOICES, PACKAGE_FOOD_CHOICES, YES_NO_CHOICES, FLIGHT_CLASS_CHOICES,
                     LEAD_SOURCE_CHOICES, LEAD_STATUS_CHOICES, TRIP_TYPE_CHOICES,
                     OPPORTUNITY_STAGE_CHOICES, PRIORITY_CHOICES,
                     QUOTATION_STATUS_CHOICES,
                     MEETING_STATUS_CHOICES, MEETING_TYPE_CHOICES,
                     GENERAL_TASK_STATUS_CHOICES, GENERAL_TASK_PRIORITY_CHOICES,
                     COMMUNICATION_TYPE_CHOICES, COMMUNICATION_DIRECTION_CHOICES,
                     DOCUMENT_TYPE_CHOICES, CONTRACT_STATUS_CHOICES)


def create_notification(user, notif_type, title, message, link=None):
    Notification.objects.create(
        user=user,
        notif_type=notif_type,
        title=title,
        message=message,
        link=link,
    )


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'leads/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    leads = Lead.objects.all()
    today = timezone.localdate()

    stats = {
        'total': leads.count(),
        'new': leads.filter(status='new').count(),
        'positive': leads.filter(status='positive').count(),
        'lost': leads.filter(status='lost').count(),
        'quotation': leads.filter(status='quotation').count(),
        'convert': leads.filter(status='converted').count(),
    }

    # Monthly lead trend (last 6 months) for histogram/bar chart
    from django.db.models import Count

    month_labels = []
    month_counts = []
    for i in range(5, -1, -1):
        y, m = today.year, today.month - i
        while m <= 0:
            m += 12
            y -= 1
        count = leads.filter(created_at__year=y, created_at__month=m).count()
        month_labels.append(f"{calendar.month_abbr[m]} {y}")
        month_counts.append(count)

    # Source breakdown for pie chart
    from .models import LEAD_SOURCE_CHOICES
    source_counts_qs = leads.values('lead_source').annotate(c=Count('id')).order_by('-c')
    source_labels = []
    source_counts = []
    source_display_map = dict(LEAD_SOURCE_CHOICES)
    for row in source_counts_qs:
        source_labels.append(source_display_map.get(row['lead_source'], row['lead_source'] or 'Unknown'))
        source_counts.append(row['c'])

    followups = FollowUp.objects.all()
    followup_stats = {
        'today': followups.filter(status='pending', follow_up_date__date=today).count(),
        'next': followups.filter(status='pending', follow_up_date__date__gt=today).count(),
        'pending': followups.filter(status='pending').count(),
        'done': followups.filter(status='done').count(),
    }

    # Travel-specific KPIs
    visa_stats = {
        'total': VisaApplication.objects.count(),
        'documents_required': VisaApplication.objects.filter(status='documents_required').count(),
        'processing': VisaApplication.objects.filter(status__in=['submitted', 'processing', 'appointment']).count(),
        'approved': VisaApplication.objects.filter(status='approved').count(),
        'rejected': VisaApplication.objects.filter(status='rejected').count(),
    }

    quotation_stats = {
        'draft': Quotation.objects.filter(status='draft').count(),
        'sent': Quotation.objects.filter(status='sent').count(),
        'approved': Quotation.objects.filter(status='approved').count(),
    }

    upcoming_departures = Booking.objects.exclude(
        booking_status__in=['cancelled', 'completed']
    ).filter(departure_date__gte=today).count()

    spo_rows = []
    for spo in SalesPerson.objects.all():
        spo_leads = Lead.objects.filter(spo=spo)
        spo_rows.append({
            'name': spo.name,
            'total': spo_leads.count(),
            'new': spo_leads.filter(status='new').count(),
            'assign': spo_leads.exclude(status='new').count(),
            'positive': spo_leads.filter(status='positive').count(),
            'lost': spo_leads.filter(status='lost').count(),
            'quotation': spo_leads.filter(status='quotation').count(),
            'convert': spo_leads.filter(status='converted').count(),
        })

    context = {
        'stats': stats,
        'followup_stats': followup_stats,
        'visa_stats': visa_stats,
        'quotation_stats': quotation_stats,
        'upcoming_departures': upcoming_departures,
        'spo_rows': spo_rows,
        'active': 'dashboard',
        'month_labels': json.dumps(month_labels),
        'month_counts': json.dumps(month_counts),
        'source_labels': json.dumps(source_labels),
        'source_counts': json.dumps(source_counts),
    }
    return render(request, 'leads/dashboard.html', context)


@login_required
def calendar_view(request):
    import calendar as cal_module
    today = timezone.localdate()

    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except (TypeError, ValueError):
        year, month = today.year, today.month

    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1

    prev_month = month - 1 or 12
    prev_year = year - 1 if month == 1 else year
    next_month = month + 1 if month < 12 else 1
    next_year = year + 1 if month == 12 else year

    cal = cal_module.Calendar(firstweekday=6)  # Sunday first
    month_days = cal.monthdatescalendar(year, month)

    events_by_day = {}

    for meeting in Meeting.objects.filter(scheduled_at__year=year, scheduled_at__month=month):
        d = meeting.scheduled_at.date()
        events_by_day.setdefault(d, []).append({
            'type': 'meeting',
            'title': meeting.title,
            'url': reverse('meeting_detail', args=[meeting.pk]),
        })

    for followup in FollowUp.objects.filter(follow_up_date__year=year, follow_up_date__month=month):
        d = followup.follow_up_date.date()
        events_by_day.setdefault(d, []).append({
            'type': 'followup',
            'title': f"Follow up: {followup.lead.name}",
            'url': reverse('lead_detail', args=[followup.lead.pk]),
        })

    for task in GeneralTask.objects.filter(due_date__year=year, due_date__month=month):
        d = task.due_date
        events_by_day.setdefault(d, []).append({
            'type': 'task',
            'title': task.title,
            'url': '',
        })

    weeks = []
    for week in month_days:
        week_data = []
        for day in week:
            week_data.append({
                'date': day,
                'day': day.day,
                'other_month': day.month != month,
                'is_today': day == today,
                'events': events_by_day.get(day, [])[:3],
                'more_count': max(0, len(events_by_day.get(day, [])) - 3),
            })
        weeks.append(week_data)

    context = {
        'active': 'calendar',
        'weeks': weeks,
        'month_name': cal_module.month_name[month],
        'year': year,
        'prev_month': prev_month, 'prev_year': prev_year,
        'next_month': next_month, 'next_year': next_year,
    }
    return render(request, 'leads/calendar.html', context)


@login_required
@block_view_only
def create_lead(request):
    if request.method == 'POST':
        form = LeadForm(request.POST)
        if form.is_valid():
            lead = form.save(commit=False)
            if not lead.spo_id and hasattr(request.user, 'salesperson'):
                lead.spo = request.user.salesperson
            lead.save()
            is_dup = check_and_mark_duplicate(lead)
            if is_dup:
                messages.warning(
                    request,
                    f'Warning: This lead may be a duplicate of an existing lead.'
                )
            else:
                assigned = assign_lead_with_ai(lead)
                if assigned:
                    messages.info(
                        request,
                        f'Lead auto-assigned to {lead.spo.name} by AI'
                    )
            _send_whatsapp_welcome(lead)
            messages.success(request, 'Lead created successfully.')
            return redirect('all_leads')
    else:
        form = LeadForm()
    spo_name = None
    if hasattr(request.user, 'salesperson'):
        spo_name = request.user.salesperson.name
    return render(request, 'leads/lead_form.html', {
        'form': form,
        'active': 'create_lead',
        'spo_name': spo_name,
    })


@login_required
def lead_delete(request, pk):
    lead = get_object_or_404(Lead, pk=pk)

    lead_name = lead.name
    lead.delete()

    messages.success(request, f'Lead "{lead_name}" deleted successfully.')
    return redirect('all_leads')


def _send_whatsapp_welcome(lead):
    """
    Sends WhatsApp welcome message to a newly created lead.
    Never raises — failure is logged but does not break lead creation.
    """
    try:
        from chatbot.services.whatsapp import send_welcome_message
        from chatbot.models import ChatSession, ChatMessage

        success, result = send_welcome_message(
            name=lead.name,
            phone=lead.contact_number,
        )

        # create a chat session for this lead
        if success:
            from chatbot.services.utils import normalize_phone
            from chatbot.services.prompts import WELCOME_MESSAGE_TEMPLATE

            normalized = normalize_phone(lead.contact_number)
            session, _ = ChatSession.objects.get_or_create(
                contact_number=normalized,
                defaults={'lead_name': lead.name}
            )
            if not session.lead_name:
                session.lead_name = lead.name
                session.save(update_fields=['lead_name'])

            welcome_text = WELCOME_MESSAGE_TEMPLATE.format(name=lead.name)
            ChatMessage.objects.create(
                session=session,
                direction='outbound',
                message=welcome_text,
                whatsapp_message_id=result,
                delivered=True,
            )
            import logging
            logging.getLogger(__name__).info(
                'Welcome message sent to lead #%s (%s)', lead.pk, lead.name
            )
        else:
            import logging
            logging.getLogger(__name__).warning(
                'Welcome message failed for lead #%s: %s', lead.pk, result
            )

    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception(
            'WhatsApp welcome error for lead #%s: %s', lead.pk, exc
        )


@login_required
def bulk_whatsapp_sender(request):
    """
    Upload an Excel file containing Name and Phone columns.
    Sends a welcome WhatsApp message to every number in the file.
    Does NOT create leads — purely for sending messages.
    """
    if request.method == 'POST':
        file = request.FILES.get('file')
        if not file:
            messages.error(request, 'Please select an Excel file.')
            return redirect('bulk_whatsapp_sender')

        try:
            import openpyxl
            wb = openpyxl.load_workbook(file, data_only=True)
            ws = wb.active
            headers = [
                str(cell.value).strip().lower() if cell.value else ''
                for cell in ws[1]
            ]
        except Exception as e:
            messages.error(request, f'Could not read file: {e}')
            return redirect('bulk_whatsapp_sender')

        from chatbot.services.whatsapp import send_welcome_message

        sent = 0
        failed = 0
        errors = []

        for row in ws.iter_rows(min_row=2, values_only=True):
            row_dict = dict(zip(headers, row))

            name = str(row_dict.get('name', '') or '').strip()
            phone = str(
                row_dict.get('phone') or
                row_dict.get('contact_number') or
                row_dict.get('number') or ''
            ).strip()

            if not name or not phone:
                failed += 1
                continue

            success, result = send_welcome_message(name=name, phone=phone)
            if success:
                sent += 1
            else:
                failed += 1
                errors.append(f'{name} ({phone}): {result}')

        if sent:
            messages.success(request, f'{sent} messages sent successfully.')
        if failed:
            messages.error(
                request,
                f'{failed} failed. ' + ' | '.join(errors[:5])
            )

        return redirect('bulk_whatsapp_sender')

    return render(request, 'leads/bulk_whatsapp_sender.html', {
        'active': 'bulk_whatsapp',
        'title': 'Bulk WhatsApp Sender',
    })


@login_required
def ai_assign_lead(request, pk):
    """Manually trigger AI assignment for a lead."""
    lead = get_object_or_404(Lead, pk=pk)
    success = assign_lead_with_ai(lead)
    if success:
        messages.success(request, f'Lead assigned to {lead.spo.name} by AI.')
    else:
        messages.error(request, 'AI assignment failed. No salespersons available.')
    return redirect('lead_detail', pk=pk)


@login_required
@block_view_only
def bulk_import_leads(request):
    if request.method == 'POST':
        file = request.FILES.get('import_file')
        if not file:
            messages.error(request, 'Please select a CSV or Excel file.')
            return redirect('create_lead')

        filename = file.name.lower()
        rows = []

        try:
            if filename.endswith('.csv'):
                decoded = file.read().decode('utf-8-sig')
                reader = csv.DictReader(io.StringIO(decoded))
                rows = list(reader)
            elif filename.endswith('.xlsx') or filename.endswith('.xls'):
                wb = openpyxl.load_workbook(file, data_only=True)
                ws = wb.active
                headers = [str(cell.value).strip() if cell.value else '' for cell in ws[1]]
                for row in ws.iter_rows(min_row=2, values_only=True):
                    row_dict = dict(zip(headers, row))
                    rows.append(row_dict)
            else:
                messages.error(request, 'Unsupported file type. Please upload a .csv or .xlsx file.')
                return redirect('create_lead')
        except Exception as e:
            messages.error(request, f'Could not read the file: {e}')
            return redirect('create_lead')

        valid_sources = dict(LEAD_SOURCE_CHOICES)
        spo = request.user.salesperson if hasattr(request.user, 'salesperson') else None

        created_count = 0
        skipped_count = 0
        errors = []

        for i, row in enumerate(rows, start=2):
            # normalize keys to lowercase, no spaces, for flexible header matching
            normalized = {
                str(k).strip().lower().replace(' ', '_'): v
                for k, v in row.items() if k
            }

            name = str(normalized.get('name', '')).strip()
            contact_number = str(normalized.get('contact_number')
                                  or normalized.get('phone')
                                  or normalized.get('contact') or '').strip()
            email = str(normalized.get('email', '')).strip()
            city = str(normalized.get('city', '')).strip()
            country = str(normalized.get('country', '')).strip()
            address = str(normalized.get('address', '')).strip()
            detail = str(normalized.get('detail') or normalized.get('notes') or '').strip()
            quotation = normalized.get('quotation') or 0

            source_raw = str(normalized.get('lead_source') or normalized.get('source') or '').strip().lower()
            lead_source = 'advertisement'
            for key, label in LEAD_SOURCE_CHOICES:
                if source_raw == key or source_raw == label.lower():
                    lead_source = key
                    break

            if not name or not contact_number:
                skipped_count += 1
                errors.append(f'Row {i}: missing name or contact number, skipped.')
                continue

            try:
                lead = Lead.objects.create(
                    name=name,
                    contact_number=contact_number,
                    email=email or None,
                    city=city or None,
                    country=country or None,
                    address=address or None,
                    detail=detail or None,
                    quotation=quotation or 0,
                    lead_source=lead_source,
                    spo=spo,
                )
                check_and_mark_duplicate(lead)
                _send_whatsapp_welcome(lead)
                created_count += 1
            except Exception as e:
                skipped_count += 1
                errors.append(f'Row {i}: {e}')

        if created_count:
            messages.success(request, f'{created_count} leads imported successfully.')
        if skipped_count:
            messages.error(request, f'{skipped_count} rows skipped. ' + ' '.join(errors[:5]))

        return redirect('all_leads')

    return redirect('create_lead')


@login_required
def lead_list(request, status=None):
    """
    Lead list with working status tabs.

    FIX: 'Positive' (and every other stage) ab correctly filter hota hai —
    URL se aaye status ya ?status= querystring, dono support hain, aur
    har tab ka live count bhi bheja jata hai.
    """
    leads = Lead.objects.select_related('spo').all()
    title = 'All Leads'
    active = 'all_leads'

    status_map = dict(LEAD_STATUS_CHOICES)

    # status URL path se bhi aa sakta hai aur ?status= se bhi
    status = status or request.GET.get('status') or ''
    status = status.strip().lower()

    if status and status in status_map:
        leads = leads.filter(status=status)
        title = f'{status_map[status]} Leads'
        active = status

    # Search
    q = request.GET.get('q')
    if q:
        leads = leads.filter(
            Q(name__icontains=q) |
            Q(contact_number__icontains=q) |
            Q(email__icontains=q) |
            Q(destination__icontains=q)
        )

    source = request.GET.get('source')
    spo = request.GET.get('spo')
    score = request.GET.get('score')
    trip = request.GET.get('trip')

    if source:
        leads = leads.filter(lead_source=source)
    if spo:
        leads = leads.filter(spo_id=spo)
    if trip:
        leads = leads.filter(trip_type=trip)

    if score == 'high':
        leads = leads.order_by('-ai_score')
    elif score == 'low':
        leads = leads.order_by('ai_score')
    else:
        leads = leads.order_by('-created_at')

    # Live counts for the tab strip (filters ignore karke, pure status counts)
    base_qs = Lead.objects.all()
    status_counts = {code: base_qs.filter(status=code).count() for code, _ in LEAD_STATUS_CHOICES}
    status_counts['all'] = base_qs.count()

    status_tabs = [{'code': 'all', 'label': 'All', 'count': status_counts['all']}]
    for code, label in LEAD_STATUS_CHOICES:
        status_tabs.append({'code': code, 'label': label, 'count': status_counts.get(code, 0)})

    context = {
        'leads': leads,
        'title': title,
        'active': active,
        'current_status': status or 'all',
        'status_tabs': status_tabs,
        'status_choices': LEAD_STATUS_CHOICES,
        'trip_types': TRIP_TYPE_CHOICES,
        'lead_sources': LEAD_SOURCE_CHOICES,
        'spos': SalesPerson.objects.all(),
    }

    return render(request, 'leads/lead_list.html', context)


@login_required
@block_view_only
def lead_edit(request, pk):
    """Edit an existing lead — status (Positive/Lost/Quotation/Converted) yahan se set hota hai."""
    lead = get_object_or_404(Lead, pk=pk)
    old_status = lead.status

    if request.method == 'POST':
        form = LeadForm(request.POST, instance=lead)
        if form.is_valid():
            lead = form.save()
            if old_status != lead.status:
                try:
                    ActivityLog.objects.create(
                        lead=lead,
                        action='status_changed',
                        description=f'Status changed from {old_status} to {lead.status}',
                        user=request.user,
                    )
                except Exception:
                    pass
            messages.success(request, f'Lead updated. Status: {lead.get_status_display()}')
            return redirect('lead_detail', pk=lead.pk)
    else:
        form = LeadForm(instance=lead)

    return render(request, 'leads/lead_form.html', {
        'form': form,
        'lead': lead,
        'is_edit': True,
        'active': 'all_leads',
    })


@login_required
@block_view_only
def update_lead_status(request, pk, status):
    lead = get_object_or_404(Lead, pk=pk)
    valid_statuses = dict(LEAD_STATUS_CHOICES)
    status = (status or '').strip().lower()
    if status in valid_statuses:
        old_status = lead.status
        lead.status = status
        lead.save(update_fields=['status', 'updated_at'])
        if old_status != status:
            try:
                ActivityLog.objects.create(
                    lead=lead,
                    action='status_changed',
                    description=f'Status changed from {old_status} to {status}',
                    user=request.user,
                )
            except Exception:
                pass
        messages.success(request, f'{lead.name} marked as {valid_statuses[status]}.')
    else:
        messages.error(request, 'Invalid lead status.')
    return redirect(request.META.get('HTTP_REFERER') or 'all_leads')


@login_required
@block_view_only
def lead_detail(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    followup_form = FollowUpForm()

    if request.method == 'POST':
        followup_form = FollowUpForm(request.POST)
        if followup_form.is_valid():
            fu = followup_form.save(commit=False)
            fu.lead = lead
            fu.save()
            messages.success(request, 'Follow-up scheduled.')
            return redirect('lead_detail', pk=pk)

    # get AI next action
    next_action = request.session.get(f'next_action_{pk}')

    if not next_action and lead.ai_score_updated:
        next_action = get_next_action(lead)

    context = {
        'lead': lead,
        'followup_form': followup_form,
        'followups': lead.followups.all(),
        'active': 'all_leads',
        'next_action': next_action,
    }
    return render(request, 'leads/lead_detail.html', context)


@login_required
def next_action_view(request, pk):
    """Get AI next action recommendation for a lead."""
    lead = get_object_or_404(Lead, pk=pk)
    next_action = get_next_action(lead)
    request.session[f'next_action_{pk}'] = next_action
    messages.success(
        request,
        f'Next Action: {next_action["action"]} — {next_action["deadline"]}'
    )
    return redirect('lead_detail', pk=pk)


@login_required
@block_view_only
def followup_done(request, pk):
    followup = get_object_or_404(FollowUp, pk=pk)
    followup.status = 'done'
    followup.save()
    messages.success(request, 'Follow-up marked done.')
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


@login_required
def followup_list(request, scope):
    """
    Follow-ups: Pending / Today / Next / Overdue / Done.

    FIX: pehle `follow_up_date.date()` UTC date deta tha jabke `today`
    local (Asia/Karachi) date tha — is wajah se Today/Next kabhi match
    nahi karte the. Ab dono taraf localtime use hota hai.
    """
    today = timezone.localdate()
    now = timezone.localtime()

    followups = FollowUp.objects.select_related('lead', 'lead__spo').all()
    title = 'All Follow Ups'
    scope = (scope or 'pending').strip().lower()

    if scope == 'pending':
        followups = followups.filter(status='pending')
        title = 'Pending Follow Ups'

    elif scope == 'today':
        followups = followups.filter(status='pending', follow_up_date__date=today)
        title = "Today's Follow Ups"

    elif scope == 'next':
        followups = followups.filter(status='pending', follow_up_date__date__gt=today)
        title = 'Upcoming Follow Ups'

    elif scope == 'overdue':
        followups = followups.filter(status='pending', follow_up_date__date__lt=today)
        title = 'Overdue Follow Ups'

    elif scope == 'done':
        followups = followups.filter(status='done')
        title = 'Completed Follow Ups'

    q = request.GET.get('q')
    if q:
        followups = followups.filter(
            Q(lead__name__icontains=q) |
            Q(lead__contact_number__icontains=q) |
            Q(notes__icontains=q)
        )

    followups = list(followups.order_by('follow_up_date'))

    for f in followups:
        local_dt = timezone.localtime(f.follow_up_date)
        f.local_dt = local_dt
        f.is_overdue = False
        if f.status == 'done':
            f.display_status = 'Done'
            f.status_class = 'done'
        elif local_dt.date() < today:
            f.display_status = 'Overdue'
            f.status_class = 'overdue'
            f.is_overdue = True
        elif local_dt.date() == today:
            f.display_status = 'Today'
            f.status_class = 'today'
        else:
            f.display_status = 'Upcoming'
            f.status_class = 'upcoming'

    pending_qs = FollowUp.objects.filter(status='pending')
    scope_counts = {
        'pending': pending_qs.count(),
        'today': pending_qs.filter(follow_up_date__date=today).count(),
        'next': pending_qs.filter(follow_up_date__date__gt=today).count(),
        'overdue': pending_qs.filter(follow_up_date__date__lt=today).count(),
        'done': FollowUp.objects.filter(status='done').count(),
    }

    scope_tabs = [
        {'code': 'pending', 'label': 'Pending', 'count': scope_counts['pending']},
        {'code': 'overdue', 'label': 'Overdue', 'count': scope_counts['overdue']},
        {'code': 'today', 'label': 'Today', 'count': scope_counts['today']},
        {'code': 'next', 'label': 'Upcoming', 'count': scope_counts['next']},
        {'code': 'done', 'label': 'Done', 'count': scope_counts['done']},
    ]

    context = {
        'followups': followups,
        'title': title,
        'active': scope,
        'current_scope': scope,
        'scope_tabs': scope_tabs,
        'scope_counts': scope_counts,
        'today': today,
        'now': now,
    }

    return render(request, 'leads/followup_list.html', context)


@login_required
def payment_list(request, ptype):
    payments = Payment.objects.select_related('lead').filter(payment_type=ptype)
    title = 'Advance Payments' if ptype == 'advance' else 'Full Payments'
    context = {'payments': payments, 'title': title, 'active': ptype}
    return render(request, 'leads/payment_list.html', context)


@login_required
@block_view_only
def add_payment(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.lead = lead
            payment.save()
            messages.success(request, 'Payment recorded.')
    return redirect('lead_detail', pk=pk)


@login_required
def scheduled_payment_list(request):
    schedules = ScheduledPayment.objects.select_related('lead').all()
    context = {'schedules': schedules, 'title': 'Scheduled Payments', 'active': 'scheduled'}
    return render(request, 'leads/scheduled_payment_list.html', context)


@login_required
@block_view_only
def scheduled_payment_create(request):
    if request.method == 'POST':
        form = ScheduledPaymentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payment plan created.')
            return redirect('scheduled_payment_list')
    else:
        form = ScheduledPaymentForm()
    context = {'form': form, 'title': 'Create Payment Plan', 'active': 'scheduled'}
    return render(request, 'leads/scheduled_payment_form.html', context)


@login_required
@block_view_only
def scheduled_payment_detail(request, pk):
    schedule = get_object_or_404(ScheduledPayment, pk=pk)
    installment_form = InstallmentForm()

    if request.method == 'POST':
        if 'add_installment' in request.POST:
            installment_form = InstallmentForm(request.POST)
            if installment_form.is_valid():
                installment = installment_form.save(commit=False)
                installment.schedule = schedule
                installment.save()
                messages.success(request, 'Installment added.')
                return redirect('scheduled_payment_detail', pk=pk)
        elif 'mark_paid' in request.POST:
            installment_id = request.POST.get('installment_id')
            installment = get_object_or_404(Installment, pk=installment_id, schedule=schedule)
            installment.is_paid = True
            installment.paid_date = timezone.localdate()
            installment.save()
            messages.success(request, 'Installment marked as paid.')
            return redirect('scheduled_payment_detail', pk=pk)

    context = {
        'schedule': schedule,
        'installments': schedule.installments.all(),
        'installment_form': installment_form,
        'active': 'scheduled',
    }
    return render(request, 'leads/scheduled_payment_detail.html', context)

SECTION_LABELS = {
    'dashboard': 'Dashboard',
    'leads': 'Leads',
    'contacts': 'Contacts & Companies',
    'pipeline': 'Pipeline & Opportunities',
    'quotations': 'Quotations',
    'meetings': 'Meetings',
    'tasks': 'Tasks',
    'payments': 'Payments',
    'followups': 'Follow Ups',
    'communications': 'Communications',
    'activity': 'Activity Logs',
    'reports': 'Reports & Analytics',
    'documents': 'Documents',
    'contracts': 'Contracts',
    'salespersons': 'Sales Persons',
    'users': 'User Management',
    'ceo_dashboard': 'CEO Dashboard',
    'whatsapp': 'WhatsApp Sender',
    'emails': 'Email Sender',
    'crm_chatbot': 'CRM Chatbot',
    'sales_chatbot': 'Sales Chatbot',
}


@login_required
@role_required('admin')
def user_list(request):
    users = User.objects.select_related('profile').all().order_by('username')
    context = {'users': users, 'active': 'users', 'title': 'Users'}
    return render(request, 'leads/user_list.html', context)


@login_required
@role_required('admin')
def user_create(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')
        phone = request.POST.get('phone')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        else:
            user = User.objects.create_user(
                username=username, email=email, password=password
            )
            user.profile.role = role
            user.profile.phone = phone
            user.profile.save()

            # save custom permissions
            _save_user_permissions(user, request.POST)

            messages.success(request, f'User {username} created.')
            return redirect('user_list')

    from .models import ROLE_CHOICES
    return render(request, 'leads/user_form.html', {
        'active': 'users',
        'title': 'Create User',
        'role_choices': ROLE_CHOICES,
        'section_labels': SECTION_LABELS,
        'permission_choices': ['full', 'view', 'none'],
    })


@login_required
@role_required('admin')
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.email = request.POST.get('email')
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.save()
        user.profile.role = request.POST.get('role')
        user.profile.phone = request.POST.get('phone')
        user.profile.save()

        # save custom permissions
        _save_user_permissions(user, request.POST)

        messages.success(request, 'User updated.')
        return redirect('user_list')

    from .models import ROLE_CHOICES
    # get current permissions
    try:
        perms = user.custom_permissions
    except Exception:
        from .models import UserPermissions
        perms, _ = UserPermissions.objects.get_or_create(user=user)

    return render(request, 'leads/user_form.html', {
        'active': 'users',
        'title': 'Edit User',
        'edit_user': user,
        'role_choices': ROLE_CHOICES,
        'section_labels': SECTION_LABELS,
        'permission_choices': ['full', 'view', 'none'],
        'current_perms': perms,
    })


def _save_user_permissions(user, post_data):
    """Saves custom section permissions from form POST data."""
    from .models import UserPermissions
    perms, _ = UserPermissions.objects.get_or_create(user=user)

    for section in UserPermissions.ALL_SECTIONS:
        value = post_data.get(f'perm_{section}', 'none')
        if value in ['full', 'view', 'none']:
            setattr(perms, section, value)

    perms.save()


@login_required
@role_required('admin')
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, "You can't delete your own account.")
    else:
        user.delete()
        messages.success(request, 'User deleted.')
    return redirect('user_list')

# ── COMPANY VIEWS ──────────────────────────────────────────

@login_required
def company_list(request):
    q = request.GET.get('q')
    companies = Company.objects.all()
    if q:
        companies = companies.filter(
            Q(name__icontains=q) | Q(email__icontains=q) | Q(city__icontains=q)
        )
    context = {'companies': companies, 'active': 'companies', 'title': 'Companies'}
    return render(request, 'leads/company_list.html', context)

@login_required
@block_view_only
def company_create(request):
    if request.method == 'POST':
        company = Company(
            name     = request.POST.get('name'),
            industry = request.POST.get('industry'),
            website  = request.POST.get('website') or None,
            email    = request.POST.get('email') or None,
            phone    = request.POST.get('phone'),
            address  = request.POST.get('address'),
            city     = request.POST.get('city'),
            country  = request.POST.get('country'),
            notes    = request.POST.get('notes'),
        )
        company.save()
        messages.success(request, f'Company "{company.name}" created.')
        return redirect('company_list')
    from .models import INDUSTRY_CHOICES
    return render(request, 'leads/company_form.html', {
        'active'          : 'companies',
        'title'           : 'Add Company',
        'industry_choices': INDUSTRY_CHOICES,
    })

@login_required
@block_view_only
def company_edit(request, pk):
    company = get_object_or_404(Company, pk=pk)
    if request.method == 'POST':
        company.name     = request.POST.get('name')
        company.industry = request.POST.get('industry')
        company.website  = request.POST.get('website') or None
        company.email    = request.POST.get('email') or None
        company.phone    = request.POST.get('phone')
        company.address  = request.POST.get('address')
        company.city     = request.POST.get('city')
        company.country  = request.POST.get('country')
        company.notes    = request.POST.get('notes')
        company.save()
        messages.success(request, 'Company updated.')
        return redirect('company_list')
    from .models import INDUSTRY_CHOICES
    return render(request, 'leads/company_form.html', {
        'active' : 'companies',
        'title'  : 'Edit Company',
        'company': company,
        'industry_choices': INDUSTRY_CHOICES,
    })

@login_required
@block_view_only
def company_delete(request, pk):
    company = get_object_or_404(Company, pk=pk)
    company.delete()
    messages.success(request, 'Company deleted.')
    return redirect('company_list')

@login_required
def company_detail(request, pk):
    company  = get_object_or_404(Company, pk=pk)
    contacts = company.contacts.all()
    context  = {'company': company, 'contacts': contacts, 'active': 'companies'}
    return render(request, 'leads/company_detail.html', context)

# ── CONTACT VIEWS ──────────────────────────────────────────

def contact_list(request):
    q = request.GET.get('q')
    contacts = Contact.objects.select_related('company').all()
    if q:
        contacts = contacts.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) |
            Q(email__icontains=q) | Q(phone__icontains=q)
        )
    context = {'contacts': contacts, 'active': 'contacts', 'title': 'Contacts'}
    return render(request, 'leads/contact_list.html', context)

@login_required
@block_view_only
def contact_create(request):
    if request.method == 'POST':
        company_id = request.POST.get('company')
        lead_id    = request.POST.get('lead')
        contact    = Contact(
            first_name = request.POST.get('first_name'),
            last_name  = request.POST.get('last_name') or None,
            email      = request.POST.get('email') or None,
            phone      = request.POST.get('phone'),
            job_title  = request.POST.get('job_title'),
            company_id = company_id if company_id else None,
            lead_id    = lead_id if lead_id else None,
            notes      = request.POST.get('notes'),
        )
        contact.save()
        messages.success(request, 'COntact created.')
        return redirect('contact_list')
    return render(request, 'leads/contact_form.html', {
        'active'   : 'contacts',
        'title'    : 'Add Contacts',
        'companies': Company.objects.all(),
        'leads'    : Lead.objects.all(),
    })

@login_required
@block_view_only
def contact_edit(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    if request.method == 'POST':
        company_id         = request.POST.get('company')
        lead_id            = request.POST.get('lead')
        contact.first_name = request.POST.get('first_name')
        contact.last_name  = request.POST.get('last_name') or None
        contact.email      = request.POST.get('email') or None
        contact.phone      = request.POST.get('phone')
        contact.company_id = company_id if company_id else None
        contact.lead_id    = lead_id if lead_id else None
        contact.notes      = request.POST.get('notes')
        contact.save()
        messages.success(request, 'Contact updated.')
        return redirect('contact_list')
    return render(request, 'leads/contact_form.html', {
        'active'   : 'contacts',
        'title'    : 'Edit Contact',
        'contact'  : contact,
        'companies': Company.objects.all(),
        'leads'    : Lead.objects.all(),
    })

@login_required
@block_view_only
def contact_delete(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    contact.delete()
    messages.success(request, 'Contact deleted.')
    return redirect('contact_list')

# ── OPPORTUNITY VIEWS ──────────────────────────────────────

@login_required
def opportunity_pipeline(request):
    """Kanban pipeline view — one column per stage."""
    stages = OPPORTUNITY_STAGE_CHOICES
    pipeline = {}
    for stage_key, stage_label in stages:
        opps = Opportunity.objects.filter(stage=stage_key).select_related(
            'lead', 'contact', 'company', 'assigned_to'
        )
        pipeline[stage_key] = {
            'label': stage_label,
            'opps': opps,
            'count': opps.count(),
            'total': sum(o.value for o in opps),
        }
    context = {
        'pipeline': pipeline,
        'stages': stages,
        'active': 'pipeline',
        'title': 'Sales Pipeline',
    }
    return render(request, 'leads/pipeline.html', context)


@login_required
def opportunity_list(request):
    opps = Opportunity.objects.select_related(
        'lead', 'contact', 'company', 'assigned_to'
    ).all()
    q = request.GET.get('q')
    if q:
        opps = opps.filter(Q(title__icontains=q) | Q(company__name__icontains=q))
    stage = request.GET.get('stage')
    if stage:
        opps = opps.filter(stage=stage)
    context = {
        'opps': opps,
        'active': 'opportunities',
        'title': 'All Opportunities',
        'stages': OPPORTUNITY_STAGE_CHOICES,
        'selected_stage': stage,
    }
    return render(request, 'leads/opportunity_list.html', context)


@login_required
@block_view_only
def opportunity_create(request):
    if request.method == 'POST':
        opp = Opportunity(
            title=request.POST.get('title'),
            stage=request.POST.get('stage', 'new'),
            priority=request.POST.get('priority', 'medium'),
            value=request.POST.get('value') or 0,
            probability=request.POST.get('probability') or 0,
            description=request.POST.get('description'),
            expected_close_date=request.POST.get('expected_close_date') or None,
        )
        lead_id = request.POST.get('lead')
        contact_id = request.POST.get('contact')
        company_id = request.POST.get('company')
        assigned_id = request.POST.get('assigned_to')
        if lead_id:
            opp.lead_id = lead_id
        if contact_id:
            opp.contact_id = contact_id
        if company_id:
            opp.company_id = company_id
        if assigned_id:
            opp.assigned_to_id = assigned_id
        opp.save()
        messages.success(request, f'Opportunity "{opp.title}" created.')
        return redirect('opportunity_pipeline')
    context = {
        'active': 'pipeline',
        'title': 'Create Opportunity',
        'stages': OPPORTUNITY_STAGE_CHOICES,
        'priorities': PRIORITY_CHOICES,
        'leads': Lead.objects.all(),
        'contacts': Contact.objects.all(),
        'companies': Company.objects.all(),
        'users': User.objects.all(),
    }
    return render(request, 'leads/opportunity_form.html', context)


@login_required
def opportunity_detail(request, pk):
    opp = get_object_or_404(Opportunity, pk=pk)
    context = {
        'opp': opp,
        'active': 'pipeline',
        'stages': OPPORTUNITY_STAGE_CHOICES,
    }
    return render(request, 'leads/opportunity_detail.html', context)


@login_required
@block_view_only
def opportunity_edit(request, pk):
    opp = get_object_or_404(Opportunity, pk=pk)
    if request.method == 'POST':
        opp.title = request.POST.get('title')
        opp.stage = request.POST.get('stage', 'new')
        opp.priority = request.POST.get('priority', 'medium')
        opp.value = request.POST.get('value') or 0
        opp.probability = request.POST.get('probability') or 0
        opp.description = request.POST.get('description')
        opp.expected_close_date = request.POST.get('expected_close_date') or None
        opp.lost_reason = request.POST.get('lost_reason') or None
        lead_id = request.POST.get('lead')
        contact_id = request.POST.get('contact')
        company_id = request.POST.get('company')
        assigned_id = request.POST.get('assigned_to')
        opp.lead_id = lead_id if lead_id else None
        opp.contact_id = contact_id if contact_id else None
        opp.company_id = company_id if company_id else None
        opp.assigned_to_id = assigned_id if assigned_id else None
        opp.save()
        messages.success(request, 'Opportunity updated.')
        return redirect('opportunity_detail', pk=pk)
    context = {
        'active': 'pipeline',
        'title': 'Edit Opportunity',
        'opp': opp,
        'stages': OPPORTUNITY_STAGE_CHOICES,
        'priorities': PRIORITY_CHOICES,
        'leads': Lead.objects.all(),
        'contacts': Contact.objects.all(),
        'companies': Company.objects.all(),
        'users': User.objects.all(),
    }
    return render(request, 'leads/opportunity_form.html', context)


@login_required
@block_view_only
def opportunity_delete(request, pk):
    opp = get_object_or_404(Opportunity, pk=pk)
    opp.delete()
    messages.success(request, 'Opportunity deleted.')
    return redirect('opportunity_pipeline')


@login_required
@block_view_only
def opportunity_move(request, pk, stage):
    """Quick stage move — called from pipeline card buttons."""
    opp = get_object_or_404(Opportunity, pk=pk)
    valid = dict(OPPORTUNITY_STAGE_CHOICES)
    if stage in valid:
        opp.stage = stage
        if stage == 'won':
            opp.probability = 100
        elif stage == 'lost':
            opp.probability = 0
        opp.save()
        messages.success(request, f'Moved to {valid[stage]}.')
    return redirect(request.META.get('HTTP_REFERER', 'opportunity_pipeline'))

# ── QUOTATION VIEWS ────────────────────────────────────────

@login_required
def quotation_list(request):
    quotations = Quotation.objects.select_related(
        'opportunity', 'company', 'contact', 'created_by'
    ).all()
    q = request.GET.get('q')
    if q:
        quotations = quotations.filter(
            Q(title__icontains=q) | Q(company__name__icontains=q)
        )
    status = request.GET.get('status')
    if status:
        quotations = quotations.filter(status=status)
    context = {
        'quotations': quotations,
        'active': 'quotations',
        'title': 'Quotations',
        'status_choices': QUOTATION_STATUS_CHOICES,
        'selected_status': status,
    }
    return render(request, 'leads/quotation_list.html', context)


@login_required
@block_view_only
def quotation_create(request):
    if request.method == 'POST':
        quotation = Quotation(
            title=request.POST.get('title'),
            status=request.POST.get('status', 'draft'),
            valid_until=request.POST.get('valid_until') or None,
            notes=request.POST.get('notes'),
            terms=request.POST.get('terms'),
            created_by=request.user,
        )
        opp_id = request.POST.get('opportunity')
        lead_id = request.POST.get('lead')
        company_id = request.POST.get('company')
        contact_id = request.POST.get('contact')
        if opp_id:
            quotation.opportunity_id = opp_id
        if lead_id:
            quotation.lead_id = lead_id
        if company_id:
            quotation.company_id = company_id
        if contact_id:
            quotation.contact_id = contact_id
        quotation.save()

        # save line items
        descriptions = request.POST.getlist('description')
        item_types = request.POST.getlist('item_type')
        quantities = request.POST.getlist('quantity')
        unit_prices = request.POST.getlist('unit_price')
        for i, (desc, qty, price) in enumerate(zip(descriptions, quantities, unit_prices)):
            if desc.strip():
                QuotationItem.objects.create(
                    quotation=quotation,
                    item_type=item_types[i] if i < len(item_types) else 'other',
                    description=desc,
                    quantity=qty or 1,
                    unit_price=price or 0,
                )

        messages.success(request, f'Quotation "{quotation.title}" created.')
        return redirect('quotation_detail', pk=quotation.pk)

    context = {
        'active': 'quotations',
        'title': 'Create Quotation',
        'status_choices': QUOTATION_STATUS_CHOICES,
        'item_type_choices': QuotationItem.ITEM_TYPE_CHOICES,
        'opportunities': Opportunity.objects.all(),
        'leads': Lead.objects.all(),
        'companies': Company.objects.all(),
        'contacts': Contact.objects.all(),
    }
    return render(request, 'leads/quotation_form.html', context)


@login_required
def quotation_detail(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)
    context = {
        'quotation': quotation,
        'items': quotation.items.all(),
        'active': 'quotations',
        'status_choices': QUOTATION_STATUS_CHOICES,
    }
    return render(request, 'leads/quotation_detail.html', context)


@login_required
def quotation_pdf(request, pk):
    from django.template.loader import render_to_string
    from django.http import HttpResponse
    quotation = get_object_or_404(Quotation, pk=pk)
    items = quotation.items.all()
    grand_total = sum(item.total_price() for item in items)
    html_string = render_to_string('leads/quotation_pdf.html', {
        'quotation': quotation,
        'items': items,
        'grand_total': grand_total,
        'company_name': 'Holiday Express Travel Agency',
    })
    try:
        from weasyprint import HTML
        pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Quotation_{quotation.pk}.pdf"'
        return response
    except ImportError:
        # Fallback: weasyprint not installed, show printable HTML instead
        return HttpResponse(html_string)


@login_required
@block_view_only
def quotation_edit(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)
    if request.method == 'POST':
        quotation.title = request.POST.get('title')
        quotation.status = request.POST.get('status', 'draft')
        quotation.valid_until = request.POST.get('valid_until') or None
        quotation.notes = request.POST.get('notes')
        quotation.terms = request.POST.get('terms')
        opp_id = request.POST.get('opportunity')
        lead_id = request.POST.get('lead')
        company_id = request.POST.get('company')
        contact_id = request.POST.get('contact')
        quotation.opportunity_id = opp_id if opp_id else None
        quotation.lead_id = lead_id if lead_id else None
        quotation.company_id = company_id if company_id else None
        quotation.contact_id = contact_id if contact_id else None
        quotation.save()

        # replace line items
        quotation.items.all().delete()
        descriptions = request.POST.getlist('description')
        item_types = request.POST.getlist('item_type')
        quantities = request.POST.getlist('quantity')
        unit_prices = request.POST.getlist('unit_price')
        for i, (desc, qty, price) in enumerate(zip(descriptions, quantities, unit_prices)):
            if desc.strip():
                QuotationItem.objects.create(
                    quotation=quotation,
                    item_type=item_types[i] if i < len(item_types) else 'other',
                    description=desc,
                    quantity=qty or 1,
                    unit_price=price or 0,
                )

        messages.success(request, 'Quotation updated.')
        return redirect('quotation_detail', pk=quotation.pk)

    context = {
        'active': 'quotations',
        'title': 'Edit Quotation',
        'quotation': quotation,
        'items': quotation.items.all(),
        'status_choices': QUOTATION_STATUS_CHOICES,
        'item_type_choices': QuotationItem.ITEM_TYPE_CHOICES,
        'opportunities': Opportunity.objects.all(),
        'leads': Lead.objects.all(),
        'companies': Company.objects.all(),
        'contacts': Contact.objects.all(),
    }
    return render(request, 'leads/quotation_form.html', context)


@login_required
@block_view_only
def quotation_delete(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)
    quotation.delete()
    messages.success(request, 'Quotation deleted.')
    return redirect('quotation_list')


@login_required
@block_view_only
def quotation_status(request, pk, status):
    quotation = get_object_or_404(Quotation, pk=pk)
    valid = dict(QUOTATION_STATUS_CHOICES)
    if status in valid:
        quotation.status = status
        quotation.save()
        messages.success(request, f'Quotation marked as {valid[status]}.')
    return redirect('quotation_detail', pk=pk)

# ── MEETING VIEWS ──────────────────────────────────────────

@login_required
def meeting_list(request):
    today = timezone.localdate()
    meetings = Meeting.objects.select_related(
        'lead', 'opportunity', 'company', 'created_by'
    ).all()

    scope = request.GET.get('scope', 'all')
    if scope == 'upcoming':
        meetings = meetings.filter(
            scheduled_at__date__gte=today,
            status='scheduled'
        )
    elif scope == 'today':
        meetings = meetings.filter(scheduled_at__date=today)
    elif scope == 'past':
        meetings = meetings.filter(scheduled_at__date__lt=today)

    q = request.GET.get('q')
    if q:
        meetings = meetings.filter(
            Q(title__icontains=q) | Q(company__name__icontains=q)
        )

    context = {
        'meetings': meetings,
        'active': 'meetings',
        'title': 'Meetings',
        'scope': scope,
    }
    return render(request, 'leads/meeting_list.html', context)


@login_required
@block_view_only
def meeting_create(request):
    if request.method == 'POST':
        scheduled_at = request.POST.get('scheduled_at')
        if not scheduled_at:
            messages.error(request, 'Please select a date and time for the meeting.')
            context = {
                'active': 'meetings',
                'title': 'Schedule Meeting',
                'meeting_types': MEETING_TYPE_CHOICES,
                'meeting_statuses': MEETING_STATUS_CHOICES,
                'leads': Lead.objects.all(),
                'opportunities': Opportunity.objects.all(),
                'companies': Company.objects.all(),
                'contacts': Contact.objects.all(),
                'users': User.objects.all(),
            }
            return render(request, 'leads/meeting_form.html', context)

        meeting = Meeting(
            title=request.POST.get('title'),
            meeting_type=request.POST.get('meeting_type', 'call'),
            status=request.POST.get('status', 'scheduled'),
            scheduled_at=scheduled_at,
            duration_minutes=request.POST.get('duration_minutes') or 30,
            location=request.POST.get('location'),
            agenda=request.POST.get('agenda'),
            notes=request.POST.get('notes'),
            action_items=request.POST.get('action_items'),
            created_by=request.user,
        )
        lead_id = request.POST.get('lead')
        opp_id = request.POST.get('opportunity')
        company_id = request.POST.get('company')
        contact_id = request.POST.get('contact')
        meeting.lead_id = lead_id if lead_id else None
        meeting.opportunity_id = opp_id if opp_id else None
        meeting.company_id = company_id if company_id else None
        meeting.contact_id = contact_id if contact_id else None
        meeting.save()
        attendee_ids = request.POST.getlist('attendees')
        if attendee_ids:
            meeting.attendees.set(attendee_ids)
        messages.success(request, 'Meeting scheduled.')
        return redirect('meeting_detail', pk=meeting.pk)

    context = {
        'active': 'meetings',
        'title': 'Schedule Meeting',
        'meeting_types': MEETING_TYPE_CHOICES,
        'meeting_statuses': MEETING_STATUS_CHOICES,
        'leads': Lead.objects.all(),
        'opportunities': Opportunity.objects.all(),
        'companies': Company.objects.all(),
        'contacts': Contact.objects.all(),
        'users': User.objects.all(),
    }
    return render(request, 'leads/meeting_form.html', context)

@login_required
def meeting_detail(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)
    context = {
        'meeting': meeting,
        'active': 'meetings',
        'meeting_statuses': MEETING_STATUS_CHOICES,
    }
    return render(request, 'leads/meeting_detail.html', context)


@login_required
@block_view_only
def meeting_edit(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)
    if request.method == 'POST':
        meeting.title = request.POST.get('title')
        meeting.meeting_type = request.POST.get('meeting_type', 'call')
        meeting.status = request.POST.get('status', 'scheduled')
        meeting.scheduled_at = request.POST.get('scheduled_at')
        meeting.duration_minutes = request.POST.get('duration_minutes') or 30
        meeting.location = request.POST.get('location')
        meeting.agenda = request.POST.get('agenda')
        meeting.notes = request.POST.get('notes')
        meeting.action_items = request.POST.get('action_items')
        lead_id = request.POST.get('lead')
        opp_id = request.POST.get('opportunity')
        company_id = request.POST.get('company')
        contact_id = request.POST.get('contact')
        meeting.lead_id = lead_id if lead_id else None
        meeting.opportunity_id = opp_id if opp_id else None
        meeting.company_id = company_id if company_id else None
        meeting.contact_id = contact_id if contact_id else None
        meeting.save()
        attendee_ids = request.POST.getlist('attendees')
        meeting.attendees.set(attendee_ids)
        messages.success(request, 'Meeting updated.')
        return redirect('meeting_detail', pk=pk)

    context = {
        'active': 'meetings',
        'title': 'Edit Meeting',
        'meeting': meeting,
        'meeting_types': MEETING_TYPE_CHOICES,
        'meeting_statuses': MEETING_STATUS_CHOICES,
        'leads': Lead.objects.all(),
        'opportunities': Opportunity.objects.all(),
        'companies': Company.objects.all(),
        'contacts': Contact.objects.all(),
        'users': User.objects.all(),
    }
    return render(request, 'leads/meeting_form.html', context)


@login_required
@block_view_only
def meeting_delete(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)
    meeting.delete()
    messages.success(request, 'Meeting deleted.')
    return redirect('meeting_list')


@login_required
@block_view_only
def meeting_status(request, pk, status):
    meeting = get_object_or_404(Meeting, pk=pk)
    valid = dict(MEETING_STATUS_CHOICES)
    if status in valid:
        meeting.status = status
        meeting.save()
        messages.success(request, f'Meeting marked as {valid[status]}.')
    return redirect('meeting_detail', pk=pk)


# ── GENERAL TASK VIEWS ─────────────────────────────────────

@login_required
def general_task_list(request):
    today = timezone.localdate()
    tasks = GeneralTask.objects.select_related('assigned_to', 'created_by').all()

    scope = request.GET.get('scope', 'all')
    if scope == 'mine':
        tasks = tasks.filter(assigned_to=request.user)
    elif scope == 'today':
        tasks = tasks.filter(due_date=today)
    elif scope == 'overdue':
        tasks = tasks.filter(due_date__lt=today, status__in=['todo', 'in_progress'])

    status = request.GET.get('status')
    if status:
        tasks = tasks.filter(status=status)

    context = {
        'tasks': tasks,
        'active': 'general_tasks',
        'title': 'Tasks',
        'scope': scope,
        'status_choices': GENERAL_TASK_STATUS_CHOICES,
        'priority_choices': GENERAL_TASK_PRIORITY_CHOICES,
        'selected_status': status,
    }
    return render(request, 'leads/general_task_list.html', context)


@login_required
@block_view_only
def general_task_create(request):
    if request.method == 'POST':
        task = GeneralTask(
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            status=request.POST.get('status', 'todo'),
            priority=request.POST.get('priority', 'medium'),
            due_date=request.POST.get('due_date') or None,
            created_by=request.user,
        )
        assigned_id = request.POST.get('assigned_to')
        lead_id = request.POST.get('lead')
        opp_id = request.POST.get('opportunity')
        task.assigned_to_id = assigned_id if assigned_id else None
        task.lead_id = lead_id if lead_id else None
        task.opportunity_id = opp_id if opp_id else None
        task.save()
        messages.success(request, 'Task created.')
        return redirect('general_task_list')

    context = {
        'active': 'general_tasks',
        'title': 'Create Task',
        'status_choices': GENERAL_TASK_STATUS_CHOICES,
        'priority_choices': GENERAL_TASK_PRIORITY_CHOICES,
        'users': User.objects.all(),
        'leads': Lead.objects.all(),
        'opportunities': Opportunity.objects.all(),
    }
    return render(request, 'leads/general_task_form.html', context)


@login_required
@block_view_only
def general_task_edit(request, pk):
    task = get_object_or_404(GeneralTask, pk=pk)
    if request.method == 'POST':
        task.title = request.POST.get('title')
        task.description = request.POST.get('description')
        task.status = request.POST.get('status', 'todo')
        task.priority = request.POST.get('priority', 'medium')
        task.due_date = request.POST.get('due_date') or None
        assigned_id = request.POST.get('assigned_to')
        lead_id = request.POST.get('lead')
        opp_id = request.POST.get('opportunity')
        task.assigned_to_id = assigned_id if assigned_id else None
        task.lead_id = lead_id if lead_id else None
        task.opportunity_id = opp_id if opp_id else None
        task.save()
        messages.success(request, 'Task updated.')
        return redirect('general_task_list')

    context = {
        'active': 'general_tasks',
        'title': 'Edit Task',
        'task': task,
        'status_choices': GENERAL_TASK_STATUS_CHOICES,
        'priority_choices': GENERAL_TASK_PRIORITY_CHOICES,
        'users': User.objects.all(),
        'leads': Lead.objects.all(),
        'opportunities': Opportunity.objects.all(),
    }
    return render(request, 'leads/general_task_form.html', context)


@login_required
@block_view_only
def general_task_delete(request, pk):
    task = get_object_or_404(GeneralTask, pk=pk)
    task.delete()
    messages.success(request, 'Task deleted.')
    return redirect('general_task_list')


@login_required
@block_view_only
def general_task_status(request, pk, status):
    task = get_object_or_404(GeneralTask, pk=pk)
    valid = dict(GENERAL_TASK_STATUS_CHOICES)
    if status in valid:
        task.status = status
        task.save()
    return redirect(request.META.get('HTTP_REFERER', 'general_task_list'))

# ── COMMUNICATION LOG VIEWS ────────────────────────────────

@login_required
def communication_list(request):
    logs = CommunicationLog.objects.select_related(
        'created_by', 'lead', 'contact', 'company', 'opportunity'
    ).all()

    comm_type = request.GET.get('type')
    if comm_type:
        logs = logs.filter(comm_type=comm_type)

    q = request.GET.get('q')
    if q:
        logs = logs.filter(
            Q(subject__icontains=q) | Q(body__icontains=q)
        )

    context = {
        'logs': logs,
        'active': 'communications',
        'title': 'Communication Log',
        'comm_types': COMMUNICATION_TYPE_CHOICES,
        'selected_type': comm_type,
    }
    return render(request, 'leads/communication_list.html', context)


@login_required
@block_view_only
def communication_create(request):
    if request.method == 'POST':
        log = CommunicationLog(
            comm_type=request.POST.get('comm_type', 'note'),
            direction=request.POST.get('direction', 'outbound'),
            subject=request.POST.get('subject'),
            body=request.POST.get('body'),
            created_by=request.user,
        )
        lead_id = request.POST.get('lead')
        opp_id = request.POST.get('opportunity')
        contact_id = request.POST.get('contact')
        company_id = request.POST.get('company')
        log.lead_id = lead_id if lead_id else None
        log.opportunity_id = opp_id if opp_id else None
        log.contact_id = contact_id if contact_id else None
        log.company_id = company_id if company_id else None
        log.save()
        messages.success(request, 'Communication logged.')

        # redirect back to wherever they came from
        next_url = request.POST.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('communication_list')

    context = {
        'active': 'communications',
        'title': 'Log Communication',
        'comm_types': COMMUNICATION_TYPE_CHOICES,
        'directions': COMMUNICATION_DIRECTION_CHOICES,
        'leads': Lead.objects.all(),
        'opportunities': Opportunity.objects.all(),
        'contacts': Contact.objects.all(),
        'companies': Company.objects.all(),
        # pre-fill from query params if coming from a detail page
        'preselect_lead': request.GET.get('lead'),
        'preselect_contact': request.GET.get('contact'),
        'preselect_company': request.GET.get('company'),
        'preselect_opportunity': request.GET.get('opportunity'),
    }
    return render(request, 'leads/communication_form.html', context)


@login_required
@block_view_only
def communication_delete(request, pk):
    log = get_object_or_404(CommunicationLog, pk=pk)
    log.delete()
    messages.success(request, 'Log deleted.')
    return redirect(request.META.get('HTTP_REFERER', 'communication_list'))


@login_required
def communication_timeline(request):
    """
    Unified timeline — filter by lead, contact, company or opportunity.
    Used as an embedded view from detail pages.
    """
    logs = CommunicationLog.objects.select_related(
        'created_by', 'lead', 'contact', 'company'
    ).all()

    lead_id = request.GET.get('lead')
    contact_id = request.GET.get('contact')
    company_id = request.GET.get('company')
    opp_id = request.GET.get('opportunity')

    if lead_id:
        logs = logs.filter(lead_id=lead_id)
    if contact_id:
        logs = logs.filter(contact_id=contact_id)
    if company_id:
        logs = logs.filter(company_id=company_id)
    if opp_id:
        logs = logs.filter(opportunity_id=opp_id)

    context = {
        'logs': logs,
        'active': 'communications',
        'title': 'Communication Timeline',
        'comm_types': COMMUNICATION_TYPE_CHOICES,
    }
    return render(request, 'leads/communication_timeline.html', context)

# ── REPORTS & ANALYTICS ────────────────────────────────────

@login_required
def reports(request):
    today = timezone.localdate()
    this_month = today.replace(day=1)

    # ── Lead Stats ──────────────────────────────────────────
    leads = Lead.objects.all()
    total_leads = leads.count()
    leads_this_month = leads.filter(created_at__date__gte=this_month).count()

    leads_by_status = {}
    for status, label in Lead._meta.get_field('status').choices:
        leads_by_status[label] = leads.filter(status=status).count()

    leads_by_source = {}
    for source, label in Lead._meta.get_field('lead_source').choices:
        count = leads.filter(lead_source=source).count()
        if count > 0:
            leads_by_source[label] = count

    # ── Pipeline Stats ──────────────────────────────────────
    opportunities = Opportunity.objects.all()
    total_pipeline_value = opportunities.exclude(
        stage__in=['lost']
    ).aggregate(total=Sum('value'))['total'] or 0

    won_value = opportunities.filter(
        stage='won'
    ).aggregate(total=Sum('value'))['total'] or 0

    total_opps = opportunities.count()
    won_opps = opportunities.filter(stage='won').count()
    win_rate = int((won_opps / total_opps) * 100) if total_opps > 0 else 0

    pipeline_by_stage = {}
    for stage, label in OPPORTUNITY_STAGE_CHOICES:
        pipeline_by_stage[label] = {
            'count': opportunities.filter(stage=stage).count(),
            'value': opportunities.filter(stage=stage).aggregate(
                total=Sum('value')
            )['total'] or 0,
        }

    # ── SPO Performance ─────────────────────────────────────
    spo_stats = []
    for spo in SalesPerson.objects.all():
        spo_leads = leads.filter(spo=spo)
        spo_stats.append({
            'name': spo.name,
            'total': spo_leads.count(),
            'new': spo_leads.filter(status='new').count(),
            'positive': spo_leads.filter(status='positive').count(),
            'converted': spo_leads.filter(status='converted').count(),
            'lost': spo_leads.filter(status='lost').count(),
            'conversion_rate': int(
                (spo_leads.filter(status='converted').count() /
                 spo_leads.count()) * 100
            ) if spo_leads.count() > 0 else 0,
        })

    # ── Payment Stats ───────────────────────────────────────
    payments = Payment.objects.all()
    total_revenue = payments.aggregate(total=Sum('amount'))['total'] or 0
    advance_revenue = payments.filter(
        payment_type='advance'
    ).aggregate(total=Sum('amount'))['total'] or 0
    full_revenue = payments.filter(
        payment_type='full'
    ).aggregate(total=Sum('amount'))['total'] or 0

    # ── Meeting Stats ───────────────────────────────────────
    meetings = Meeting.objects.all()
    meeting_by_type = {}
    for mtype, label in MEETING_TYPE_CHOICES:
        count = meetings.filter(meeting_type=mtype).count()
        if count > 0:
            meeting_by_type[label] = count

    # ── Followup Stats ───────────────────────────────────────
    followups = FollowUp.objects.all()
    followup_done = followups.filter(status='done').count()
    followup_pending = followups.filter(status='pending').count()

    context = {
        'active': 'reports',
        'title': 'Reports & Analytics',

        # leads
        'total_leads': total_leads,
        'leads_this_month': leads_this_month,
        'leads_by_status': leads_by_status,
        'leads_by_source': leads_by_source,

        # pipeline
        'total_pipeline_value': total_pipeline_value,
        'won_value': won_value,
        'win_rate': win_rate,
        'total_opps': total_opps,
        'won_opps': won_opps,
        'pipeline_by_stage': pipeline_by_stage,

        # spo
        'spo_stats': spo_stats,

        # payments
        'total_revenue': total_revenue,
        'advance_revenue': advance_revenue,
        'full_revenue': full_revenue,

        # projects

        # meetings
        'meeting_by_type': meeting_by_type,

        # followups
        'followup_done': followup_done,
        'followup_pending': followup_pending,
    }
    return render(request, 'leads/reports.html', context)

# ── ACTIVITY LOG VIEW ──────────────────────────────────────

@login_required
def activity_log(request):
    logs = ActivityLog.objects.select_related('user').all()

    entity_type = request.GET.get('entity')
    if entity_type:
        logs = logs.filter(entity_type=entity_type)

    action = request.GET.get('action')
    if action:
        logs = logs.filter(action=action)

    # only show last 500 to keep it fast
    logs = logs[:500]

    entity_types = ActivityLog.objects.values_list(
        'entity_type', flat=True
    ).distinct().order_by('entity_type')

    context = {
        'logs': logs,
        'active': 'activity_log',
        'title': 'Activity Log',
        'entity_types': entity_types,
        'action_choices': ActivityLog.ACTION_CHOICES,
        'selected_entity': entity_type,
        'selected_action': action,
    }
    return render(request, 'leads/activity_log.html', context)

# ── DOCUMENT VIEWS ─────────────────────────────────────────

@login_required
@block_view_only
def document_upload(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        doc_type = request.POST.get('doc_type', 'other')
        notes = request.POST.get('notes')
        file = request.FILES.get('file')

        if not file:
            messages.error(request, 'Please select a file to upload.')
            return redirect(request.META.get('HTTP_REFERER', 'document_list'))

        doc = Document(
            title=title or file.name,
            doc_type=doc_type,
            notes=notes,
            uploaded_by=request.user,
            file=file,
        )
        lead_id = request.POST.get('lead')
        opp_id = request.POST.get('opportunity')
        project_id = request.POST.get('project')
        ticket_id = request.POST.get('ticket')
        quotation_id = request.POST.get('quotation')
        doc.lead_id = lead_id if lead_id else None
        doc.opportunity_id = opp_id if opp_id else None
        doc.project_id = project_id if project_id else None
        doc.ticket_id = ticket_id if ticket_id else None
        doc.quotation_id = quotation_id if quotation_id else None
        doc.save()
        messages.success(request, f'"{doc.title}" uploaded successfully.')

        next_url = request.POST.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('document_list')

    context = {
        'active': 'documents',
        'title': 'Upload Document',
        'doc_types': DOCUMENT_TYPE_CHOICES,
        'leads': Lead.objects.all(),
        'opportunities': Opportunity.objects.all(),
        'quotations': Quotation.objects.all(),
        'preselect_lead': request.GET.get('lead'),
        'preselect_opportunity': request.GET.get('opportunity'),
        'preselect_quotation': request.GET.get('quotation'),
    }
    return render(request, 'leads/document_upload.html', context)


@login_required
def document_list(request):
    documents = Document.objects.select_related(
        'uploaded_by', 'lead', 'opportunity'
    ).all()

    doc_type = request.GET.get('type')
    if doc_type:
        documents = documents.filter(doc_type=doc_type)

    q = request.GET.get('q')
    if q:
        documents = documents.filter(Q(title__icontains=q))

    context = {
        'documents': documents,
        'active': 'documents',
        'title': 'Documents',
        'doc_types': DOCUMENT_TYPE_CHOICES,
        'selected_type': doc_type,
    }
    return render(request, 'leads/document_list.html', context)


@login_required
@block_view_only
def document_delete(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    doc.file.delete()
    doc.delete()
    messages.success(request, 'Document deleted.')
    return redirect(request.META.get('HTTP_REFERER', 'document_list'))

# ── CONTRACT VIEWS ─────────────────────────────────────────

@login_required
def contract_list(request):
    contracts = Contract.objects.select_related(
        'company', 'opportunity', 'created_by'
    ).all()

    status = request.GET.get('status')
    if status:
        contracts = contracts.filter(status=status)

    q = request.GET.get('q')
    if q:
        contracts = contracts.filter(Q(title__icontains=q))

    context = {
        'contracts': contracts,
        'active': 'contracts',
        'title': 'Contracts',
        'status_choices': CONTRACT_STATUS_CHOICES,
        'selected_status': status,
    }
    return render(request, 'leads/contract_list.html', context)


@login_required
@block_view_only
def contract_create(request):
    if request.method == 'POST':
        contract = Contract(
            title=request.POST.get('title'),
            status=request.POST.get('status', 'draft'),
            value=request.POST.get('value') or 0,
            start_date=request.POST.get('start_date') or None,
            end_date=request.POST.get('end_date') or None,
            signed_date=request.POST.get('signed_date') or None,
            terms=request.POST.get('terms'),
            notes=request.POST.get('notes'),
            created_by=request.user,
        )
        opp_id = request.POST.get('opportunity')
        quot_id = request.POST.get('quotation')
        company_id = request.POST.get('company')
        contact_id = request.POST.get('contact')
        contract.opportunity_id = opp_id if opp_id else None
        contract.quotation_id = quot_id if quot_id else None
        contract.company_id = company_id if company_id else None
        contract.contact_id = contact_id if contact_id else None

        if request.FILES.get('signed_file'):
            contract.signed_file = request.FILES['signed_file']

        contract.save()
        messages.success(request, f'Contract "{contract.title}" created.')
        return redirect('contract_detail', pk=contract.pk)

    context = {
        'active': 'contracts',
        'title': 'Create Contract',
        'status_choices': CONTRACT_STATUS_CHOICES,
        'opportunities': Opportunity.objects.filter(stage='won'),
        'quotations': Quotation.objects.all(),
        'companies': Company.objects.all(),
        'contacts': Contact.objects.all(),
    }
    return render(request, 'leads/contract_form.html', context)


@login_required
def contract_detail(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    context = {
        'contract': contract,
        'active': 'contracts',
        'status_choices': CONTRACT_STATUS_CHOICES,
    }
    return render(request, 'leads/contract_detail.html', context)


@login_required
@block_view_only
def contract_edit(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if request.method == 'POST':
        contract.title = request.POST.get('title')
        contract.status = request.POST.get('status', 'draft')
        contract.value = request.POST.get('value') or 0
        contract.start_date = request.POST.get('start_date') or None
        contract.end_date = request.POST.get('end_date') or None
        contract.signed_date = request.POST.get('signed_date') or None
        contract.terms = request.POST.get('terms')
        contract.notes = request.POST.get('notes')
        opp_id = request.POST.get('opportunity')
        quot_id = request.POST.get('quotation')
        company_id = request.POST.get('company')
        contact_id = request.POST.get('contact')
        contract.opportunity_id = opp_id if opp_id else None
        contract.quotation_id = quot_id if quot_id else None
        contract.company_id = company_id if company_id else None
        contract.contact_id = contact_id if contact_id else None
        if request.FILES.get('signed_file'):
            contract.signed_file = request.FILES['signed_file']
        contract.save()
        messages.success(request, 'Contract updated.')
        return redirect('contract_detail', pk=pk)

    context = {
        'active': 'contracts',
        'title': 'Edit Contract',
        'contract': contract,
        'status_choices': CONTRACT_STATUS_CHOICES,
        'opportunities': Opportunity.objects.filter(stage='won'),
        'quotations': Quotation.objects.all(),
        'companies': Company.objects.all(),
        'contacts': Contact.objects.all(),
    }
    return render(request, 'leads/contract_form.html', context)


@login_required
@block_view_only
def contract_delete(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    contract.delete()
    messages.success(request, 'Contract deleted.')
    return redirect('contract_list')


@login_required
@block_view_only
def contract_status(request, pk, status):
    contract = get_object_or_404(Contract, pk=pk)
    valid = dict(CONTRACT_STATUS_CHOICES)
    if status in valid:
        contract.status = status
        if status == 'signed':
            contract.signed_date = timezone.localdate()
        contract.save()
        if status == 'signed':
            for admin_user in User.objects.filter(profile__role__in=['admin', 'ceo']):
                create_notification(
                    user=admin_user,
                    notif_type='contract_signed',
                    title=f'Contract signed: {contract.title}',
                    message=f'Contract "{contract.title}" has been signed.',
                    link=f'/contracts/{contract.pk}/',
                )
        messages.success(request, f'Contract marked as {valid[status]}.')
    return redirect('contract_detail', pk=pk)


# ── NOTIFICATION VIEWS ─────────────────────────────────────

@login_required
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user)
    context = {
        'notifications': notifications,
        'active': 'notifications',
        'title': 'Notifications'
    }
    return render(request, 'leads/notification_list.html', context)


@login_required
def notification_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save()
    if notif.link:
        return redirect(notif.link)
    return redirect('notification_list')


@login_required
def notification_read_all(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, 'All notifications marked as read.')
    return redirect('notification_list')


@login_required
def notification_delete(request, pk):
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.delete()
    return redirect('notification_list')


@login_required
def score_lead_view(request, pk):
    """Manually trigger AI scoring for a lead."""
    lead = get_object_or_404(Lead, pk=pk)
    success = update_lead_score(lead)
    if success:
        messages.success(
            request,
            f'Lead scored: {lead.ai_score}/100 — {lead.ai_score_reason}'
        )
    else:
        messages.error(request, 'Scoring failed. Check OpenAI API key.')
    return redirect('lead_detail', pk=pk)


@login_required
def score_all_leads(request):
    """Score all leads in bulk — admin only."""
    leads = Lead.objects.all()
    count = 0
    for lead in leads:
        if update_lead_score(lead):
            count += 1
    messages.success(request, f'{count} leads scored successfully.')
    return redirect('all_leads')


@login_required
def salesperson_list(request):
    salespersons = SalesPerson.objects.select_related('user').all()

    spo_data = []
    for spo in salespersons:
        total = spo.leads.count()
        converted = spo.leads.filter(status='converted').count()
        rate = round((converted / total * 100), 1) if total > 0 else 0
        spo_data.append({
            'spo': spo,
            'total': total,
            'converted': converted,
            'rate': rate,
        })

    context = {
        'spo_data': spo_data,
        'active': 'salespersons',
        'title': 'Sales Persons',
    }
    return render(request, 'leads/salesperson_list.html', context)


@login_required
def salesperson_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        user_id = request.POST.get('user')
        if not name:
            messages.error(request, 'Name is required.')
            return redirect('salesperson_create')
        spo = SalesPerson(name=name)
        if user_id:
            spo.user_id = user_id
        spo.save()
        messages.success(request, f'Sales Person "{name}" created.')
        return redirect('salesperson_list')

    users = User.objects.all()
    return render(request, 'leads/salesperson_form.html', {
        'active': 'salespersons',
        'title': 'Add Sales Person',
        'users': users,
    })


@login_required
def salesperson_edit(request, pk):
    spo = get_object_or_404(SalesPerson, pk=pk)
    if request.method == 'POST':
        spo.name = request.POST.get('name')
        user_id = request.POST.get('user')
        spo.user_id = user_id if user_id else None
        spo.save()
        messages.success(request, 'Sales Person updated.')
        return redirect('salesperson_list')

    users = User.objects.all()
    return render(request, 'leads/salesperson_form.html', {
        'active': 'salespersons',
        'title': 'Edit Sales Person',
        'spo': spo,
        'users': users,
    })


@login_required
def salesperson_delete(request, pk):
    spo = get_object_or_404(SalesPerson, pk=pk)
    spo.delete()
    messages.success(request, 'Sales Person deleted.')
    return redirect('salesperson_list')


@login_required
def closing_probability_view(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    success = update_closing_probability(lead)
    if success:
        messages.success(
            request,
            f'Closing probability: {lead.closing_probability}% — {lead.closing_probability_reason}'
        )
    else:
        messages.error(request, 'Prediction failed.')
    return redirect('lead_detail', pk=pk)


@login_required
def ai_followup_message_view(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    channel = request.GET.get('channel', 'whatsapp')
    message = generate_followup_message(lead, channel=channel)
    context = {
        'lead': lead,
        'message': message,
        'channel': channel,
        'active': 'all_leads',
    }
    return render(request, 'leads/ai_followup_message.html', context)


@login_required
def ai_meeting_summary_view(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)
    success = save_meeting_summary(meeting)
    if success:
        messages.success(request, 'Meeting summary generated.')
    else:
        messages.error(request, 'Summary generation failed.')
    return redirect('meeting_detail', pk=pk)


@login_required
def sales_forecast_view(request):
    forecast = generate_sales_forecast()
    context = {
        'forecast': forecast,
        'active': 'reports',
        'title': 'AI Sales Forecast',
    }
    return render(request, 'leads/sales_forecast.html', context)


@login_required
def churn_risk_view(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    success = update_churn_risk(lead)
    if success:
        messages.success(
            request,
            f'Churn risk: {lead.churn_risk} — {lead.churn_risk_reason}'
        )
    else:
        messages.error(request, 'Churn prediction failed.')
    return redirect('lead_detail', pk=pk)


@login_required
def churn_risk_all_view(request):
    """Shows all leads with high churn risk."""
    high_risk = get_high_churn_leads(limit=50)
    context = {
        'leads': high_risk,
        'active': 'churn',
        'title': 'High Churn Risk Leads',
    }
    return render(request, 'leads/churn_risk_list.html', context)


@login_required
def upsell_recommendations_view(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    recommendations = get_upsell_recommendations(lead)
    context = {
        'lead': lead,
        'recommendations': recommendations,
        'active': 'all_leads',
        'title': f'Upsell Opportunities — {lead.name}',
    }
    return render(request, 'leads/upsell_recommendations.html', context)


@login_required
def lifetime_value_view(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    success = update_lifetime_value(lead)
    if success:
        messages.success(
            request,
            f'Lifetime value estimated: {lead.lifetime_value}'
        )
    else:
        messages.error(request, 'LTV estimation failed.')
    return redirect('lead_detail', pk=pk)


@login_required
def customer_360_view(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    context = {
        'lead': lead,
        'followups': lead.followups.all(),
        'payments': lead.payments.all(),
        'communications': lead.communications.all(),
        'meetings': lead.meetings.all(),
        'documents': lead.documents.all(),
        'quotations': lead.quotations.all(),
        'scheduled_payments': lead.scheduled_payments.all(),
        'active': 'all_leads',
        'title': f'360° View — {lead.name}',
    }
    return render(request, 'leads/customer_360.html', context)


@login_required
def ceo_dashboard(request):
    from django.db.models import Sum, Count
    from django.utils import timezone

    today = timezone.localdate()
    this_month = today.replace(day=1)

    # ── Revenue ────────────────────────────────────────────
    total_revenue = Payment.objects.aggregate(
        total=Sum('amount')
    )['total'] or 0

    this_month_revenue = Payment.objects.filter(
        date__date__gte=this_month
    ).aggregate(total=Sum('amount'))['total'] or 0

    advance_revenue = Payment.objects.filter(
        payment_type='advance'
    ).aggregate(total=Sum('amount'))['total'] or 0

    full_revenue = Payment.objects.filter(
        payment_type='full'
    ).aggregate(total=Sum('amount'))['total'] or 0

    # ── Pipeline ───────────────────────────────────────────
    leads = Lead.objects.all()
    total_leads = leads.count()
    new_leads = leads.filter(status='new').count()
    positive_leads = leads.filter(status='positive').count()
    converted_leads = leads.filter(status='converted').count()
    lost_leads = leads.filter(status='lost').count()
    quotation_leads = leads.filter(status='quotation').count()

    conversion_rate = round(
        (converted_leads / total_leads * 100)
        if total_leads > 0 else 0, 1
    )

    pipeline_value = leads.filter(
        status__in=['positive', 'quotation']
    ).aggregate(total=Sum('quotation'))['total'] or 0

    # ── Team Performance ───────────────────────────────────
    spo_performance = []
    for spo in SalesPerson.objects.all():
        spo_leads = leads.filter(spo=spo)
        spo_total = spo_leads.count()
        spo_converted = spo_leads.filter(status='converted').count()
        spo_rate = round(
            (spo_converted / spo_total * 100)
            if spo_total > 0 else 0, 1
        )
        spo_revenue = Payment.objects.filter(
            lead__spo=spo
        ).aggregate(total=Sum('amount'))['total'] or 0

        spo_performance.append({
            'name': spo.name,
            'total': spo_total,
            'converted': spo_converted,
            'rate': spo_rate,
            'revenue': spo_revenue,
        })

    # sort by revenue descending
    spo_performance.sort(key=lambda x: x['revenue'], reverse=True)

    # ── Churn Alerts ───────────────────────────────────────
    high_churn_leads = get_high_churn_leads(limit=5)

    # ── Top Scored Leads ───────────────────────────────────
    top_leads = leads.filter(
        ai_score__gt=0
    ).order_by('-ai_score')[:5]

    # ── Activity Today ─────────────────────────────────────
    meetings_today = Meeting.objects.filter(
        scheduled_at__date=today,
        status='scheduled'
    ).count()

    tasks_overdue = GeneralTask.objects.filter(
        due_date__lt=today,
        status__in=['todo', 'in_progress']
    ).count()

    followups_today = FollowUp.objects.filter(
        follow_up_date__date=today,
        status='pending'
    ).count()

    # ── AI Forecast ────────────────────────────────────────
    forecast = generate_sales_forecast()

    context = {
        'active': 'ceo_dashboard',
        'title': 'CEO Dashboard',

        # revenue
        'total_revenue': total_revenue,
        'this_month_revenue': this_month_revenue,
        'advance_revenue': advance_revenue,
        'full_revenue': full_revenue,

        # pipeline
        'total_leads': total_leads,
        'new_leads': new_leads,
        'positive_leads': positive_leads,
        'converted_leads': converted_leads,
        'lost_leads': lost_leads,
        'quotation_leads': quotation_leads,
        'conversion_rate': conversion_rate,
        'pipeline_value': pipeline_value,

        # team
        'spo_performance': spo_performance,

        # ai
        'high_churn_leads': high_churn_leads,
        'top_leads': top_leads,
        'forecast': forecast,

        # activity
        'meetings_today': meetings_today,
        'tasks_overdue': tasks_overdue,
        'followups_today': followups_today,
    }
    return render(request, 'leads/ceo_dashboard.html', context)


# ── AI PROPOSAL WRITER ─────────────────────────────────────

@login_required
def proposal_writer(request, lead_pk=None):
    """
    Main proposal writer page.
    Accepts optional lead_pk to pre-link the proposal to a lead.
    """
    lead = None
    if lead_pk:
        lead = get_object_or_404(Lead, pk=lead_pk)

    if request.method == 'POST':
        title = request.POST.get('title', 'Business Proposal')
        manual_notes = request.POST.get('manual_notes', '')
        pdf_file = request.FILES.get('pdf_file')
        lead_id = request.POST.get('lead_id')

        if lead_id:
            lead = Lead.objects.filter(pk=lead_id).first()

        # create proposal record
        proposal = Proposal(
            title=title,
            lead=lead,
            manual_notes=manual_notes,
            created_by=request.user,
            status='draft',
        )

        # handle PDF upload and extraction
        pdf_text = ''
        if pdf_file:
            proposal.uploaded_pdf = pdf_file
            proposal.save()  # save to disk first
            pdf_path = proposal.uploaded_pdf.path
            pdf_text = extract_pdf_text(pdf_path)
            proposal.pdf_extracted_text = pdf_text
        else:
            proposal.save()

        # build lead context for AI
        lead_context = None
        if lead:
            lead_context = {
                'name': lead.name,
                'company': lead.city or '',
                'email': lead.email or '',
                'quotation': str(lead.quotation),
                'source': lead.get_lead_source_display(),
            }

        # generate proposal with OpenAI
        generated_text = generate_proposal(
            manual_notes=manual_notes,
            pdf_text=pdf_text,
            lead_context=lead_context,
        )

        proposal.generated_proposal = generated_text
        proposal.status = 'generated'
        proposal.save()

        return redirect('proposal_detail', pk=proposal.pk)

    context = {
        'lead': lead,
        'leads': Lead.objects.all(),
        'active': 'proposals',
        'title': 'AI Proposal Writer',
    }
    return render(request, 'leads/proposal_writer.html', context)


@login_required
def proposal_detail(request, pk):
    """View and edit the generated proposal."""
    proposal = get_object_or_404(Proposal, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save':
            proposal.generated_proposal = request.POST.get(
                'generated_proposal', proposal.generated_proposal
            )
            proposal.title = request.POST.get('title', proposal.title)
            proposal.save()
            messages.success(request, 'Proposal saved.')

        elif action == 'approve':
            proposal.generated_proposal = request.POST.get(
                'generated_proposal', proposal.generated_proposal
            )
            proposal.status = 'approved'
            proposal.save()
            messages.success(request, 'Proposal approved.')

        elif action == 'regenerate':
            proposal.manual_notes = request.POST.get(
                'manual_notes', proposal.manual_notes
            )
            pdf_text = proposal.pdf_extracted_text or ''

            lead_context = None
            if proposal.lead:
                lead_context = {
                    'name': proposal.lead.name,
                    'email': proposal.lead.email or '',
                    'quotation': str(proposal.lead.quotation),
                    'source': proposal.lead.get_lead_source_display(),
                }

            generated_text = generate_proposal(
                manual_notes=proposal.manual_notes or '',
                pdf_text=pdf_text,
                lead_context=lead_context,
            )
            proposal.generated_proposal = generated_text
            proposal.status = 'generated'
            proposal.save()
            messages.success(request, 'Proposal regenerated.')

        return redirect('proposal_detail', pk=pk)

    context = {
        'proposal': proposal,
        'active': 'proposals',
        'title': proposal.title,
    }
    return render(request, 'leads/proposal_detail.html', context)


@login_required
def proposal_list(request):
    """List all proposals."""
    proposals = Proposal.objects.select_related('lead', 'created_by').all()
    context = {
        'proposals': proposals,
        'active': 'proposals',
        'title': 'Proposals',
    }
    return render(request, 'leads/proposal_list.html', context)


@login_required
def proposal_delete(request, pk):
    proposal = get_object_or_404(Proposal, pk=pk)
    proposal.delete()
    messages.success(request, 'Proposal deleted.')
    return redirect('proposal_list')


@login_required
def assistant_config(request):
    try:
        perms = request.user.custom_permissions
    except Exception:
        from .models import UserPermissions
        perms, _ = UserPermissions.objects.get_or_create(user=request.user)

    crm_access = perms.crm_chatbot
    sales_access = perms.sales_chatbot

    if request.user.is_superuser or getattr(getattr(request.user, 'profile', None), 'role', None) == 'admin':
        crm_access = 'full'
        sales_access = 'full'

    return JsonResponse({
        'crm_access': crm_access,
        'sales_access': sales_access,
        'show_selector': crm_access != 'none' and sales_access != 'none',
    })


@login_required
@require_POST
def assistant_chat(request):
    data = json.loads(request.body)
    assistant_type = data.get('assistant_type')
    message = data.get('message', '').strip()
    conversation_id = data.get('conversation_id')

    if assistant_type not in ('crm', 'sales'):
        return JsonResponse({'error': 'Invalid assistant type'}, status=400)
    if not message:
        return JsonResponse({'error': 'Empty message'}, status=400)

    # permission check
    is_admin = request.user.is_superuser or getattr(getattr(request.user, 'profile', None), 'role', None) == 'admin'
    if not is_admin:
        try:
            perms = request.user.custom_permissions
        except Exception:
            from .models import UserPermissions
            perms, _ = UserPermissions.objects.get_or_create(user=request.user)
        level = perms.crm_chatbot if assistant_type == 'crm' else perms.sales_chatbot
        if level == 'none':
            return JsonResponse({'error': 'You do not have access to this assistant.'}, status=403)

    service = AssistantService(request.user, assistant_type)
    result = service.handle_message(message, conversation_id)
    return JsonResponse(result)


@login_required
def assistant_history(request, conversation_id):
    conversation = AssistantConversation.objects.filter(id=conversation_id, user=request.user).first()
    if not conversation:
        return JsonResponse({'messages': []})
    messages = list(conversation.messages.values('role', 'content', 'created_at'))
    return JsonResponse({'messages': messages})

@login_required
def email_inbox(request):
    try:
        perms = request.user.custom_permissions
        if not (request.user.is_superuser or perms.has_access('emails')):
            messages.error(request, "You don't have access to Email Sender.")
            return redirect('dashboard')
    except Exception:
        pass

    emails = EmailLog.objects.all().order_by('-created_at')

    # Non-admin users only see emails they personally sent
    is_admin = request.user.is_superuser or getattr(getattr(request.user, 'profile', None), 'role', None) == 'admin'
    if not is_admin:
        emails = emails.filter(sent_by=request.user)

    return render(request, 'leads/email_inbox.html', {
        'emails': emails,
        'active': 'emails',
    })
from django.core.mail import get_connection, EmailMessage

def _get_user_email_account(user):
    key = getattr(getattr(user, 'profile', None), 'email_account_key', 'default') or 'default'
    return key, settings.EMAIL_ACCOUNTS.get(key, settings.EMAIL_ACCOUNTS['default'])


@login_required
def email_compose(request, lead_id=None):
    try:
        perms = request.user.custom_permissions
        if not (request.user.is_superuser or perms.has_access('emails')):
            messages.error(request, "You don't have access to Email Sender.")
            return redirect('dashboard')
        if request.method == 'POST' and not request.user.is_superuser and perms.is_view_only('emails'):
            messages.error(request, "You have view-only access to Email Sender.")
            return redirect('email_inbox')
    except Exception:
        pass

    lead = None
    if lead_id:
        lead = get_object_or_404(Lead, id=lead_id)

    account_key, account = _get_user_email_account(request.user)

    if request.method == 'POST':
        to_email = request.POST.get('to_email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        status = 'sent'
        try:
            connection = get_connection(
                host=account['HOST'],
                port=account['PORT'],
                username=account['HOST_USER'],
                password=account['HOST_PASSWORD'],
                use_tls=account['USE_TLS'],
            )
            email_msg = EmailMessage(
                subject=subject,
                body=message,
                from_email=account['HOST_USER'],   # <-- yehi bdo@bilalenterprise.com bhejega
                to=[to_email],
                connection=connection,
            )
            email_msg.send(fail_silently=False)
            messages.success(request, 'Email sent successfully.')
        except Exception as e:
            status = 'failed'
            messages.error(request, f'Email failed: {e}')

        EmailLog.objects.create(
            lead=lead,
            sent_by=request.user,
            to_email=to_email,
            from_email=account['HOST_USER'],
            subject=subject,
            message=message,
            status=status,
            direction='outbound',
            account_key=account_key,
        )
        return redirect('email_inbox')

    return render(request, 'leads/email_compose.html', {
        'lead': lead,
        'active': 'emails',
        'sender_email': account['HOST_USER'],   # template mein dikhane ke liye
    })

@login_required
def email_detail(request, pk):
    try:
        perms = request.user.custom_permissions
        if not (request.user.is_superuser or perms.has_access('emails')):
            messages.error(request, "You don't have access to Email Sender.")
            return redirect('dashboard')
    except Exception:
        pass
    email = get_object_or_404(EmailLog, pk=pk)
    return render(request, 'leads/email_detail.html', {
        'email': email,
        'active': 'emails',
    })
    
    
@login_required
def email_delete(request, pk):
    try:
        perms = request.user.custom_permissions
        if not (request.user.is_superuser or perms.has_access('emails')):
            messages.error(request, "You don't have access to Email Sender.")
            return redirect('dashboard')
        if not request.user.is_superuser and perms.is_view_only('emails'):
            messages.error(request, "You have view-only access to Email Sender.")
            return redirect('email_inbox')
    except Exception:
        pass

    email = get_object_or_404(EmailLog, pk=pk)

    is_admin = request.user.is_superuser or getattr(getattr(request.user, 'profile', None), 'role', None) == 'admin'
    if not is_admin and email.sent_by_id != request.user.id:
        messages.error(request, "You can only delete emails you sent.")
        return redirect('email_inbox')

    email.delete()
    messages.success(request, 'Email deleted successfully.')
    return redirect('email_inbox')


@login_required
@require_POST
def email_bulk_delete(request):
    try:
        perms = request.user.custom_permissions
        if not (request.user.is_superuser or perms.has_access('emails')):
            messages.error(request, "You don't have access to Email Sender.")
            return redirect('dashboard')
        if not request.user.is_superuser and perms.is_view_only('emails'):
            messages.error(request, "You have view-only access to Email Sender.")
            return redirect('email_inbox')
    except Exception:
        pass

    ids = request.POST.getlist('email_ids')
    if not ids:
        messages.error(request, 'No emails selected.')
        return redirect('email_inbox')

    qs = EmailLog.objects.filter(pk__in=ids)

    is_admin = request.user.is_superuser or getattr(getattr(request.user, 'profile', None), 'role', None) == 'admin'
    if not is_admin:
        qs = qs.filter(sent_by=request.user)  # user apni emails hi delete kar sakta hai

    count = qs.count()
    qs.delete()
    messages.success(request, f'{count} email(s) deleted successfully.')
    return redirect('email_inbox')
    
    

# ============================================================
# 1. PHONE CALLING (Twilio) — click-to-call + recording
# ============================================================

@login_required
@require_POST
def start_phone_call(request, lead_id):
    """Agent clicks 'Call' on a lead — Twilio dials the lead and bridges to the agent."""
    lead = get_object_or_404(Lead, id=lead_id)
    agent_number = request.POST.get('agent_number') or settings.AGENT_FALLBACK_NUMBER

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    call = client.calls.create(
        to=lead.contact_number,
        from_=settings.TWILIO_PHONE_NUMBER,
        url=settings.SITE_BASE_URL + reverse('twiml_response') + f'?agent_number={agent_number}',
        status_callback=settings.SITE_BASE_URL + reverse('call_status_callback', args=[lead.id]),
        status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
        status_callback_method='POST',
        record=True,
        recording_status_callback=settings.SITE_BASE_URL + reverse('recording_callback'),
        recording_status_callback_method='POST',
    )

    log = CallLog.objects.create(
        lead=lead,
        caller=request.user,
        call_sid=call.sid,
        to_number=lead.contact_number,
        channel='phone',
        status='initiated',
    )
    return JsonResponse({'status': 'calling', 'call_sid': call.sid, 'log_id': log.id})


@csrf_exempt
def twiml_response(request):
    """Twilio requests this URL when the call connects — decides what happens on the call."""
    agent_number = request.GET.get('agent_number') or settings.AGENT_FALLBACK_NUMBER
    response = VoiceResponse()
    dial = Dial(caller_id=settings.TWILIO_PHONE_NUMBER)
    dial.number(agent_number)
    response.append(dial)
    return HttpResponse(str(response), content_type='text/xml')


@csrf_exempt
@require_POST
def call_status_callback(request, lead_id):
    call_sid = request.POST.get('CallSid')
    call_status = request.POST.get('CallStatus')
    duration = request.POST.get('CallDuration', 0)

    CallLog.objects.filter(call_sid=call_sid).update(
        status=call_status,
        duration=duration or 0,
    )
    return HttpResponse(status=200)


@csrf_exempt
@require_POST
def recording_callback(request):
    call_sid = request.POST.get('CallSid')
    recording_sid = request.POST.get('RecordingSid')
    recording_url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Recordings/{recording_sid}.mp3"

    CallLog.objects.filter(call_sid=call_sid).update(recording_url=recording_url)
    return HttpResponse(status=200)


# ============================================================
# 2. WHATSAPP CALLING (Meta Cloud API)
# ============================================================
# Real WhatsApp voice calls via Meta's Cloud API use WebRTC. The backend below
# initiates/manages the call session; actual audio requires an SDP offer from a
# WebRTC-capable client (browser mic/speaker access), which then gets relayed
# through these endpoints. This is NOT optional plumbing — without a WebRTC
# frontend, the call session can open but no audio will flow.

META_GRAPH_URL = f"https://graph.facebook.com/{settings.META_WA_API_VERSION}/{settings.META_WA_PHONE_NUMBER_ID}/calls"


def _meta_headers():
    return {
        'Authorization': f'Bearer {settings.META_WA_ACCESS_TOKEN}',
        'Content-Type': 'application/json',
    }


@login_required
@require_POST
def start_whatsapp_call(request, lead_id):
    """
    Initiates a WhatsApp call session. `sdp_offer` must come from your frontend's
    WebRTC client (RTCPeerConnection.createOffer()) — pass it in as POST data.
    """
    lead = get_object_or_404(Lead, id=lead_id)
    sdp_offer = request.POST.get('sdp_offer')

    if not sdp_offer:
        return JsonResponse(
            {'error': 'sdp_offer is required — generate it client-side via WebRTC before calling this endpoint.'},
            status=400,
        )

    payload = {
        "messaging_product": "whatsapp",
        "to": lead.contact_number.replace('+', '').replace(' ', ''),
        "action": "connect",
        "session": {
            "sdp_type": "offer",
            "sdp": sdp_offer,
        },
    }

    resp = requests.post(META_GRAPH_URL, headers=_meta_headers(), data=json.dumps(payload))
    data = resp.json()

    if resp.status_code != 200:
        return JsonResponse({'error': 'meta_api_error', 'details': data}, status=resp.status_code)

    call_id = data.get('calls', [{}])[0].get('id', '')

    CallLog.objects.create(
        lead=lead,
        caller=request.user,
        call_sid=call_id,
        to_number=lead.contact_number,
        channel='whatsapp',
        status='initiated',
    )
    # Meta returns the callee's SDP answer asynchronously via webhook (see below),
    # not in this response — your WebRTC client must wait for it to complete the connection.
    return JsonResponse({'status': 'initiated', 'call_id': call_id})


@login_required
@require_POST
def end_whatsapp_call(request, call_id):
    payload = {
        "messaging_product": "whatsapp",
        "call_id": call_id,
        "action": "terminate",
    }
    resp = requests.post(META_GRAPH_URL, headers=_meta_headers(), data=json.dumps(payload))
    CallLog.objects.filter(call_sid=call_id).update(status='completed')
    return JsonResponse(resp.json(), status=resp.status_code)


@csrf_exempt
def whatsapp_webhook(request):
    """
    Single webhook endpoint for both verification (GET) and events (POST) —
    register this URL in Meta App Dashboard > WhatsApp > Configuration.
    Handles call status updates (ringing/accepted/rejected/terminated) and
    delivers the SDP answer your WebRTC client needs to complete the call.
    """
    if request.method == 'GET':
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        if mode == 'subscribe' and token == settings.META_WA_VERIFY_TOKEN:
            return HttpResponse(challenge)
        return HttpResponse('Verification failed', status=403)

    if request.method == 'POST':
        body = json.loads(request.body.decode('utf-8'))
        try:
            entry = body['entry'][0]['changes'][0]['value']
            calls = entry.get('calls', [])
            for call_event in calls:
                call_id = call_event.get('id')
                event_status = call_event.get('status')  # ringing, accepted, rejected, terminated
                if call_id and event_status:
                    CallLog.objects.filter(call_sid=call_id).update(status=event_status)

                # SDP answer arrives here when the callee accepts — push it to the
                # waiting frontend client via websockets/polling/Server-Sent-Events
                # so RTCPeerConnection.setRemoteDescription() can be called.
                session = call_event.get('session', {})
                if session.get('sdp_type') == 'answer':
                    # TODO: relay session['sdp'] to the agent's browser (e.g. via Django Channels)
                    pass
        except (KeyError, IndexError, json.JSONDecodeError):
            pass

        return HttpResponse(status=200)


# ============================================================
# 3. GOOGLE CALENDAR — OAuth flow + scheduling
# ============================================================

def _build_flow():
    return Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
            }
        },
        scopes=settings.GOOGLE_SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )


@login_required
def google_authorize(request):
    """'Connect Google Calendar' button points here."""
    flow = _build_flow()
    auth_url, state = flow.authorization_url(
        access_type='offline',       # needed to get a refresh_token
        prompt='consent',            # forces refresh_token on repeat auth too
        include_granted_scopes='true',
    )
    request.session['google_oauth_state'] = state
    return redirect(auth_url)


@login_required
def google_callback(request):
    state = request.session.get('google_oauth_state')
    flow = _build_flow()
    flow.fetch_token(authorization_response=request.build_absolute_uri())

    credentials = flow.credentials
    GoogleCredential.objects.update_or_create(
        user=request.user,
        defaults={
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_expiry': credentials.expiry,
        },
    )
    return redirect('dashboard')


def _get_calendar_service(user):
    cred = GoogleCredential.objects.get(user=user)
    creds = Credentials(
        token=cred.access_token,
        refresh_token=cred.refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=settings.GOOGLE_SCOPES,
    )
    service = build('calendar', 'v3', credentials=creds)

    # Persist refreshed access token if it rotated
    if creds.token != cred.access_token:
        cred.access_token = creds.token
        cred.save(update_fields=['access_token'])

    return service


@login_required
@require_POST
def schedule_call(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id)
    scheduled_time = parse_datetime(request.POST.get('scheduled_time'))  # "2026-07-25T15:00:00"
    note = request.POST.get('note', '')

    if not scheduled_time:
        return JsonResponse({'error': 'Invalid scheduled_time format'}, status=400)

    try:
        service = _get_calendar_service(request.user)
    except GoogleCredential.DoesNotExist:
        return JsonResponse({'error': 'Google Calendar not connected'}, status=400)

    event = {
        'summary': f'Call: {lead.name}',
        'description': note or f'Follow-up call with {lead.name} ({lead.contact_number})',
        'start': {'dateTime': scheduled_time.isoformat(), 'timeZone': 'Asia/Karachi'},
        'end': {'dateTime': (scheduled_time + timedelta(minutes=15)).isoformat(), 'timeZone': 'Asia/Karachi'},
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': 30},
                {'method': 'popup', 'minutes': 10},
            ],
        },
    }
    created_event = service.events().insert(calendarId='primary', body=event).execute()

    schedule = CallSchedule.objects.create(
        lead=lead,
        scheduled_by=request.user,
        scheduled_time=scheduled_time,
        note=note,
        google_event_id=created_event['id'],
    )
    return JsonResponse({
        'status': 'scheduled',
        'schedule_id': schedule.id,
        'event_link': created_event.get('htmlLink'),
    })


@login_required
@require_POST
def cancel_scheduled_call(request, schedule_id):
    schedule = get_object_or_404(CallSchedule, id=schedule_id, scheduled_by=request.user)
    if schedule.google_event_id:
        try:
            service = _get_calendar_service(request.user)
            service.events().delete(calendarId='primary', eventId=schedule.google_event_id).execute()
        except Exception:
            pass  # event may already be deleted on Google's side
    schedule.delete()
    return JsonResponse({'status': 'cancelled'})



####  call_log_list  #####
@login_required
def call_log_list(request):
    calls = CallLog.objects.select_related('lead').order_by('-created_at')

    channel = request.GET.get('channel')
    if channel:
        calls = calls.filter(channel=channel)

    status = request.GET.get('status')
    if status:
        calls = calls.filter(status=status)

    paginator = Paginator(calls, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'leads/call_log_list.html', {
        'page_obj': page_obj,
        'active': 'call_logs',
        'channel_filter': channel,
    })


@login_required
def call_schedule_list(request):
    schedules = CallSchedule.objects.select_related('lead').order_by('scheduled_time')

    scope = request.GET.get('scope')
    if scope == 'mine':
        schedules = schedules.filter(scheduled_by=request.user)

    paginator = Paginator(schedules, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'leads/call_schedule_list.html', {
        'page_obj': page_obj,
        'active': 'scheduled_calls',
    })


# ============================================================
# BOOKING MODULE
# ============================================================

@login_required
def booking_list(request):
    bookings = Booking.objects.filter(is_deleted=False).select_related('client', 'company')
    trash_count = Booking.objects.filter(is_deleted=True).count()

    q = request.GET.get('q')
    if q:
        bookings = bookings.filter(
            Q(package_name__icontains=q) |
            Q(client__first_name__icontains=q) |
            Q(client__last_name__icontains=q) |
            Q(company__name__icontains=q)
        )

    return render(request, 'leads/booking_list.html', {
        'bookings': bookings,
        'trash_count': trash_count,
        'active': 'booking',
    })


@login_required
def booking_trash(request):
    bookings = Booking.objects.filter(is_deleted=True).select_related('client', 'company')
    return render(request, 'leads/booking_trash.html', {
        'bookings': bookings,
        'active': 'booking',
    })


@login_required
def booking_restore(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    booking.is_deleted = False
    booking.save(update_fields=['is_deleted'])
    messages.success(request, 'Booking restored.')
    return redirect('booking_trash')


@login_required
def booking_delete(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    booking.is_deleted = True
    booking.save(update_fields=['is_deleted'])
    messages.success(request, 'Booking moved to trash.')
    return redirect('booking_list')


@login_required
def booking_delete_permanent(request, pk):
    booking = get_object_or_404(Booking, pk=pk, is_deleted=True)
    booking.delete()
    messages.success(request, 'Booking permanently deleted.')
    return redirect('booking_trash')


def _parse_decimal(value):
    try:
        return Decimal(str(value).strip() or '0')
    except (InvalidOperation, ValueError, TypeError):
        return Decimal('0')


def _parse_int(value, default=1):
    try:
        return max(1, int(value))
    except (ValueError, TypeError):
        return default


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def _parse_time(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%H:%M').time()
    except (ValueError, TypeError):
        return None


@login_required
def booking_create(request):
    if request.method == 'POST':
        booking = Booking(
            package_type=request.POST.get('package_type', 'umrah'),
            year=_parse_int(request.POST.get('year'), default=timezone.now().year),
            package_name=request.POST.get('package_name', '').strip(),
            booking_status=request.POST.get('booking_status', 'pending'),

            booking_for=request.POST.get('booking_for', 'client'),
            no_of_pax=_parse_int(request.POST.get('no_of_pax'), default=1),
            care_of=request.POST.get('care_of', '').strip(),
            passport_number=request.POST.get('passport_number', '').strip(),
            cnic_number=request.POST.get('cnic_number', '').strip(),
            phone_number=request.POST.get('phone_number', '').strip(),
            emergency_phone=request.POST.get('emergency_phone', '').strip(),
            voucher_number=request.POST.get('voucher_number', '').strip(),
            card_number=request.POST.get('card_number', '').strip(),

            departure_date=_parse_date(request.POST.get('departure_date')),
            departure_flight_no=request.POST.get('departure_flight_no', '').strip(),
            departure_time=_parse_time(request.POST.get('departure_time')),
            departure_airline=request.POST.get('departure_airline', '').strip(),
            departure_pnr=request.POST.get('departure_pnr', '').strip(),
            arrival_date=_parse_date(request.POST.get('arrival_date')),
            arrival_flight_no=request.POST.get('arrival_flight_no', '').strip(),
            arrival_time=_parse_time(request.POST.get('arrival_time')),
            arrival_airline=request.POST.get('arrival_airline', '').strip(),
            arrival_pnr=request.POST.get('arrival_pnr', '').strip(),

            package_cost_per_person=_parse_decimal(request.POST.get('package_cost_per_person')),
            visa_charges_total=_parse_decimal(request.POST.get('visa_charges_total')),
            flight_charges_total=_parse_decimal(request.POST.get('flight_charges_total')),
            other_charges=_parse_decimal(request.POST.get('other_charges')),
            total_received=_parse_decimal(request.POST.get('total_received')),

            created_by=request.user,
        )

        client_id = request.POST.get('client')
        if client_id:
            booking.client = Contact.objects.filter(pk=client_id).first()

        company_id = request.POST.get('company')
        if company_id:
            booking.company = Company.objects.filter(pk=company_id).first()

        booking.save()

        # Persons
        person_names = request.POST.getlist('person_full_name[]')
        person_passports = request.POST.getlist('person_passport[]')
        person_cnics = request.POST.getlist('person_cnic[]')
        person_phones = request.POST.getlist('person_phone[]')
        for i, name in enumerate(person_names):
            if not name.strip():
                continue
            BookingPerson.objects.create(
                booking=booking,
                is_main=(i == 0),
                full_name=name.strip(),
                passport_number=person_passports[i] if i < len(person_passports) else '',
                cnic_number=person_cnics[i] if i < len(person_cnics) else '',
                phone_number=person_phones[i] if i < len(person_phones) else '',
            )

        # Flight passenger tickets
        ticket_names = request.POST.getlist('ticket_passenger[]')
        ticket_passports = request.POST.getlist('ticket_passport[]')
        ticket_seats = request.POST.getlist('ticket_seat[]')
        for i, name in enumerate(ticket_names):
            if not name.strip():
                continue
            BookingTicket.objects.create(
                booking=booking,
                passenger_name=name.strip(),
                passport_number=ticket_passports[i] if i < len(ticket_passports) else '',
                ticket_seat=ticket_seats[i] if i < len(ticket_seats) else '',
            )

        # Hotels
        hotel_cities = request.POST.getlist('hotel_city[]')
        hotel_names = request.POST.getlist('hotel_name[]')
        hotel_nights = request.POST.getlist('hotel_nights[]')
        hotel_room_types = request.POST.getlist('hotel_room_type[]')
        hotel_rooms = request.POST.getlist('hotel_rooms[]')
        hotel_checkins = request.POST.getlist('hotel_checkin[]')
        hotel_checkouts = request.POST.getlist('hotel_checkout[]')
        for i, city in enumerate(hotel_cities):
            if not (city.strip() or (i < len(hotel_names) and hotel_names[i].strip())):
                continue
            BookingHotel.objects.create(
                booking=booking,
                city=city.strip() or 'Makkah',
                hotel_name=hotel_names[i] if i < len(hotel_names) else '',
                nights=_parse_int(hotel_nights[i] if i < len(hotel_nights) else 1),
                room_type=hotel_room_types[i] if i < len(hotel_room_types) else 'single',
                no_of_rooms=_parse_int(hotel_rooms[i] if i < len(hotel_rooms) else 1),
                check_in=_parse_date(hotel_checkins[i] if i < len(hotel_checkins) else None),
                check_out=_parse_date(hotel_checkouts[i] if i < len(hotel_checkouts) else None),
            )

        # Transport routes
        route_texts = request.POST.getlist('route_text[]')
        route_types = request.POST.getlist('route_type[]')
        route_notes = request.POST.getlist('route_notes[]')
        for i, route_text in enumerate(route_texts):
            if not route_text.strip():
                continue
            BookingRoute.objects.create(
                booking=booking,
                route=route_text.strip(),
                transport_type=route_types[i] if i < len(route_types) else 'private_car',
                notes=route_notes[i] if i < len(route_notes) else '',
            )

        # Visa entries
        visa_passports = request.POST.getlist('visa_passport[]')
        visa_names = request.POST.getlist('visa_name[]')
        visa_dobs = request.POST.getlist('visa_dob[]')
        visa_companies = request.POST.getlist('visa_company[]')
        visa_send_tos = request.POST.getlist('visa_send_to[]')
        visa_statuses = request.POST.getlist('visa_status[]')
        for i, name in enumerate(visa_names):
            if not name.strip():
                continue
            BookingVisa.objects.create(
                booking=booking,
                passport_number=visa_passports[i] if i < len(visa_passports) else '',
                full_name=name.strip(),
                date_of_birth=_parse_date(visa_dobs[i] if i < len(visa_dobs) else None),
                visa_company=visa_companies[i] if i < len(visa_companies) else '',
                send_to=visa_send_tos[i] if i < len(visa_send_tos) else '',
                status=visa_statuses[i] if i < len(visa_statuses) else 'pending',
            )

        messages.success(request, 'Booking saved successfully.')
        return redirect('booking_list')

    contacts = Contact.objects.all().order_by('first_name')
    companies = Company.objects.all().order_by('name')
    return render(request, 'leads/booking_form.html', {
        'contacts': contacts,
        'companies': companies,
        'active': 'booking',
        'current_year': timezone.now().year,
    })


# ============================================================
# PACKAGE MODULE (Hajj / Umrah Packages)
# ============================================================

def _parse_datetime_local(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%dT%H:%M')
    except (ValueError, TypeError):
        return None


def _parse_optional_int(value):
    if value in (None, ''):
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


@login_required
def package_list(request):
    packages = Package.objects.filter(is_deleted=False).select_related('company')
    trash_count = Package.objects.filter(is_deleted=True).count()

    q = request.GET.get('q')
    if q:
        packages = packages.filter(
            Q(package_name__icontains=q) |
            Q(package_code__icontains=q) |
            Q(maktab__icontains=q)
        )

    return render(request, 'leads/package_list.html', {
        'packages': packages,
        'trash_count': trash_count,
        'active': 'packages',
    })


@login_required
def package_trash(request):
    packages = Package.objects.filter(is_deleted=True).select_related('company')
    return render(request, 'leads/package_trash.html', {
        'packages': packages,
        'active': 'packages',
    })


@login_required
def package_restore(request, pk):
    package = get_object_or_404(Package, pk=pk)
    package.is_deleted = False
    package.save(update_fields=['is_deleted'])
    messages.success(request, 'Package restored.')
    return redirect('package_trash')


@login_required
def package_delete(request, pk):
    package = get_object_or_404(Package, pk=pk)
    package.is_deleted = True
    package.save(update_fields=['is_deleted'])
    messages.success(request, 'Package moved to trash.')
    return redirect('package_list')


@login_required
def package_delete_permanent(request, pk):
    package = get_object_or_404(Package, pk=pk, is_deleted=True)
    package.delete()
    messages.success(request, 'Package permanently deleted.')
    return redirect('package_trash')


def _save_package_from_post(request, package):
    package.company_id = request.POST.get('company') or None
    package.package_number = request.POST.get('package_number', '').strip()
    package.category = request.POST.get('category', '').strip()
    package.zone = request.POST.get('zone', '').strip()
    package.package_name = request.POST.get('package_name', '').strip()
    package.package_code = request.POST.get('package_code', '').strip()
    package.days = _parse_optional_int(request.POST.get('days'))
    package.year = _parse_int(request.POST.get('year'), default=timezone.now().year)
    package.maktab = request.POST.get('maktab', '').strip()
    package.maktab_number = request.POST.get('maktab_number', '').strip()
    package.medina_arrival = request.POST.get('medina_arrival', 'before_hajj')
    package.hajj_duration = request.POST.get('hajj_duration', 'short')
    package.hijri_start_day = _parse_optional_int(request.POST.get('hijri_start_day'))
    package.hijri_start_month = request.POST.get('hijri_start_month', '').strip()

    package.room_type = request.POST.get('room_type', '').strip()
    package.azizia_room_type = request.POST.get('azizia_room_type', '').strip()
    package.makkah_type = request.POST.get('makkah_type', '').strip()
    package.medinah_type = request.POST.get('medinah_type', '').strip()
    package.azizia_type = request.POST.get('azizia_type', '').strip()
    package.mina_type = request.POST.get('mina_type', '').strip()

    for zone_key in ('makkah_a', 'makkah_b', 'madinah_a', 'madinah_b'):
        for room_key in ('double', 'triple', 'quad', 'sharing'):
            field = f'{zone_key}_{room_key}'
            setattr(package, field, _parse_int(request.POST.get(field, '0'), default=0) if request.POST.get(field, '0').strip() else 0)

    package.giveaways = request.POST.get('giveaways', '').strip()
    package.terms_condition = request.POST.get('terms_condition', '').strip()
    package.itinerary_description = request.POST.get('itinerary_description', '').strip()

    for image_field, form_field in [
        ('itinerary_image_mina', 'itinerary_image_mina'),
        ('itinerary_image_arafat', 'itinerary_image_arafat'),
        ('itinerary_image_muzdalifah', 'itinerary_image_muzdalifah'),
        ('itinerary_image_rami_day1', 'itinerary_image_rami_day1'),
        ('itinerary_image_rami_day2', 'itinerary_image_rami_day2'),
        ('itinerary_image_rami_day3', 'itinerary_image_rami_day3'),
    ]:
        if form_field in request.FILES:
            setattr(package, image_field, request.FILES[form_field])

    package.maktab_address = request.POST.get('maktab_address', '').strip()
    package.office_address = request.POST.get('office_address', '').strip()

    if not package.pk:
        package.created_by = request.user

    package.save()

    # Accommodation (repeatable)
    package.accommodations.all().delete()
    places = request.POST.getlist('accommodation_place[]')
    check_ins = request.POST.getlist('accommodation_check_in[]')
    check_outs = request.POST.getlist('accommodation_check_out[]')
    same_hotels = request.POST.getlist('accommodation_same_hotel[]')
    types_a = request.POST.getlist('accommodation_type_a[]')
    ratings_a = request.POST.getlist('accommodation_rating_a[]')
    hotels_a = request.POST.getlist('accommodation_hotel_a[]')
    types_b = request.POST.getlist('accommodation_type_b[]')
    ratings_b = request.POST.getlist('accommodation_rating_b[]')
    hotels_b = request.POST.getlist('accommodation_hotel_b[]')
    distances = request.POST.getlist('accommodation_distance[]')
    azizia_dates = request.POST.getlist('accommodation_azizia_date[]')
    food_packages = request.POST.getlist('accommodation_food[]')
    acc_days = request.POST.getlist('accommodation_days[]')
    actual_ins = request.POST.getlist('accommodation_actual_checkin[]')
    actual_outs = request.POST.getlist('accommodation_actual_checkout[]')
    nights_list = request.POST.getlist('accommodation_nights[]')
    makkah_ziarats = request.POST.getlist('accommodation_makkah_ziarat[]')
    madinah_ziarats = request.POST.getlist('accommodation_madinah_ziarat[]')
    distributions = request.POST.getlist('accommodation_distribution[]')
    camps = request.POST.getlist('accommodation_camp[]')
    arafats = request.POST.getlist('accommodation_arafat[]')
    shuttles = request.POST.getlist('accommodation_shuttle[]')
    beddings = request.POST.getlist('accommodation_bedding[]')
    sharings = request.POST.getlist('accommodation_sharing[]')
    sharing_types = request.POST.getlist('accommodation_sharing_type[]')
    notes = request.POST.getlist('accommodation_note[]')

    def _get(lst, i, default=''):
        return lst[i] if i < len(lst) else default

    for i in range(len(places)):
        if not (places[i].strip() or _get(hotels_a, i).strip() or _get(hotels_b, i).strip()):
            continue
        PackageAccommodation.objects.create(
            package=package,
            place=places[i],
            check_in=_parse_date(_get(check_ins, i)),
            check_out=_parse_date(_get(check_outs, i)),
            same_hotel_for_both=(_get(same_hotels, i) == 'on'),
            accommodation_type_a=_get(types_a, i),
            saudi_star_rating_a=_get(ratings_a, i),
            hotel_a=_get(hotels_a, i),
            accommodation_type_b=_get(types_b, i),
            saudi_star_rating_b=_get(ratings_b, i),
            hotel_b=_get(hotels_b, i),
            distance_meter=_parse_optional_int(_get(distances, i)),
            azizia_date=_parse_date(_get(azizia_dates, i)),
            food_package=_get(food_packages, i),
            accommodation_days=_parse_optional_int(_get(acc_days, i)),
            actual_check_in_time=_parse_datetime_local(_get(actual_ins, i)),
            actual_check_out_time=_parse_datetime_local(_get(actual_outs, i)),
            nights=_parse_optional_int(_get(nights_list, i)),
            makkah_ziarat=_get(makkah_ziarats, i),
            madinah_ziarat=_get(madinah_ziarats, i),
            distribution=_get(distributions, i),
            camp=_get(camps, i),
            arafat=_get(arafats, i),
            azizia_shuttle=_get(shuttles, i),
            bedding_sofa_mattress=_get(beddings, i),
            sharing_room_tent_camp=_get(sharings, i),
            sharing_type=_get(sharing_types, i),
            note=_get(notes, i),
        )

    # Transport (repeatable)
    package.transports.all().delete()
    routes = request.POST.getlist('transport_route[]')
    arrivals = request.POST.getlist('transport_arrival[]')
    departures = request.POST.getlist('transport_departure[]')
    trans_types = request.POST.getlist('transport_type[]')
    vehicles = request.POST.getlist('transport_vehicle[]')
    for i in range(len(routes)):
        if not (routes[i].strip() or _get(vehicles, i).strip()):
            continue
        PackageTransport.objects.create(
            package=package,
            route=routes[i],
            arrival=_get(arrivals, i),
            departure=_get(departures, i),
            type=_get(trans_types, i),
            vehicle=_get(vehicles, i),
        )

    # Flights (repeatable)
    package.flights.all().delete()
    airlines = request.POST.getlist('flight_airline[]')
    flight_nos = request.POST.getlist('flight_no[]')
    flight_classes = request.POST.getlist('flight_class[]')
    f_origins = request.POST.getlist('flight_origin[]')
    f_destinations = request.POST.getlist('flight_destination[]')
    f_dep_dates = request.POST.getlist('flight_departure_date[]')
    f_dep_times = request.POST.getlist('flight_departure_time[]')
    f_arr_dates = request.POST.getlist('flight_arrival_date[]')
    f_arr_times = request.POST.getlist('flight_arrival_time[]')
    f_pnrs = request.POST.getlist('flight_pnr[]')
    f_amounts = request.POST.getlist('flight_amount[]')
    f_preferred = request.POST.getlist('flight_preferred[]')
    for i in range(len(airlines)):
        if not (airlines[i].strip() or _get(flight_nos, i).strip()):
            continue
        PackageFlight.objects.create(
            package=package,
            airline=airlines[i],
            flight_no=_get(flight_nos, i),
            flight_class=_get(flight_classes, i),
            origin=_get(f_origins, i),
            destination=_get(f_destinations, i),
            departure_date=_parse_date(_get(f_dep_dates, i)),
            departure_time=_parse_time(_get(f_dep_times, i)),
            arrival_date=_parse_date(_get(f_arr_dates, i)),
            arrival_time=_parse_time(_get(f_arr_times, i)),
            pnr_no=_get(f_pnrs, i),
            ticket_amount=_parse_decimal(_get(f_amounts, i)),
            is_preferred=_get(f_preferred, i, 'no'),
        )

    # Trains (repeatable)
    package.trains.all().delete()
    railways = request.POST.getlist('train_railway[]')
    train_nos = request.POST.getlist('train_no[]')
    train_classes = request.POST.getlist('train_class[]')
    t_origins = request.POST.getlist('train_origin[]')
    t_destinations = request.POST.getlist('train_destination[]')
    t_dep_dates = request.POST.getlist('train_departure_date[]')
    t_dep_times = request.POST.getlist('train_departure_time[]')
    t_arr_dates = request.POST.getlist('train_arrival_date[]')
    t_arr_times = request.POST.getlist('train_arrival_time[]')
    t_pnrs = request.POST.getlist('train_pnr[]')
    t_amounts = request.POST.getlist('train_amount[]')
    for i in range(len(railways)):
        if not (railways[i].strip() or _get(train_nos, i).strip()):
            continue
        PackageTrain.objects.create(
            package=package,
            railway=railways[i],
            train_no=_get(train_nos, i),
            train_class=_get(train_classes, i),
            origin=_get(t_origins, i),
            destination=_get(t_destinations, i),
            departure_date=_parse_date(_get(t_dep_dates, i)),
            departure_time=_parse_time(_get(t_dep_times, i)),
            arrival_date=_parse_date(_get(t_arr_dates, i)),
            arrival_time=_parse_time(_get(t_arr_times, i)),
            pnr_no=_get(t_pnrs, i),
            ticket_amount=_parse_decimal(_get(t_amounts, i)),
        )

    return package


@login_required
def package_create(request):
    if request.method == 'POST':
        package = Package()
        _save_package_from_post(request, package)
        messages.success(request, 'Package saved successfully.')
        return redirect('package_list')

    companies = Company.objects.all().order_by('name')
    return render(request, 'leads/package_form.html', {
        'companies': companies,
        'active': 'packages',
        'current_year': timezone.now().year,
        'package': None,
        'medina_arrival_choices': MEDINA_ARRIVAL_CHOICES,
        'hajj_duration_choices': HAJJ_DURATION_CHOICES,
        'hijri_month_choices': HIJRI_MONTH_CHOICES,
        'room_sharing_choices': PACKAGE_ROOM_SHARING_CHOICES,
        'place_choices': PACKAGE_PLACE_CHOICES,
        'accommodation_type_choices': PACKAGE_ACCOMMODATION_TYPE_CHOICES,
        'star_rating_choices': SAUDI_STAR_RATING_CHOICES,
        'food_choices': PACKAGE_FOOD_CHOICES,
        'yes_no_choices': YES_NO_CHOICES,
        'flight_class_choices': FLIGHT_CLASS_CHOICES,
    })


@login_required
def package_edit(request, pk):
    package = get_object_or_404(Package, pk=pk)
    if request.method == 'POST':
        _save_package_from_post(request, package)
        messages.success(request, 'Package updated successfully.')
        return redirect('package_list')

    companies = Company.objects.all().order_by('name')
    return render(request, 'leads/package_form.html', {
        'companies': companies,
        'active': 'packages',
        'current_year': timezone.now().year,
        'package': package,
        'medina_arrival_choices': MEDINA_ARRIVAL_CHOICES,
        'hajj_duration_choices': HAJJ_DURATION_CHOICES,
        'hijri_month_choices': HIJRI_MONTH_CHOICES,
        'room_sharing_choices': PACKAGE_ROOM_SHARING_CHOICES,
        'place_choices': PACKAGE_PLACE_CHOICES,
        'accommodation_type_choices': PACKAGE_ACCOMMODATION_TYPE_CHOICES,
        'star_rating_choices': SAUDI_STAR_RATING_CHOICES,
        'food_choices': PACKAGE_FOOD_CHOICES,
        'yes_no_choices': YES_NO_CHOICES,
        'flight_class_choices': FLIGHT_CLASS_CHOICES,
    })


@login_required
def package_view(request, pk):
    package = get_object_or_404(Package, pk=pk)
    return render(request, 'leads/package_detail.html', {
        'package': package,
        'active': 'packages',
    })


# ============================================================
# VISA MANAGEMENT MODULE
# ============================================================

DEFAULT_VISA_CHECKLIST = [
    'Passport (original + copy)', 'Passport-size photographs', 'CNIC / ID copy',
    'Bank statement', 'Confirmed hotel booking', 'Confirmed flight booking',
    'Employment letter / NOC',
]


@login_required
def visa_list(request):
    applications = VisaApplication.objects.select_related('lead', 'assigned_agent').all()
    q = request.GET.get('q')
    if q:
        applications = applications.filter(
            Q(applicant_name__icontains=q) | Q(country__icontains=q) | Q(passport_number__icontains=q)
        )
    status = request.GET.get('status')
    if status:
        applications = applications.filter(status=status)
    country = request.GET.get('country')
    if country:
        applications = applications.filter(country__icontains=country)

    context = {
        'applications': applications,
        'active': 'visa',
        'title': 'Visa Applications',
        'status_choices': VISA_APPLICATION_STATUS_CHOICES,
        'selected_status': status,
    }
    return render(request, 'leads/visa_list.html', context)


@login_required
@block_view_only
def visa_create(request):
    if request.method == 'POST':
        application = VisaApplication(
            applicant_name=request.POST.get('applicant_name'),
            passport_number=request.POST.get('passport_number'),
            country=request.POST.get('country'),
            visa_category=request.POST.get('visa_category', 'tourist'),
            application_type=request.POST.get('application_type'),
            embassy_fee=request.POST.get('embassy_fee') or 0,
            service_fee=request.POST.get('service_fee') or 0,
            processing_time_days=request.POST.get('processing_time_days') or None,
            status=request.POST.get('status', 'documents_required'),
            appointment_datetime=request.POST.get('appointment_datetime') or None,
            submission_date=request.POST.get('submission_date') or None,
            expected_decision_date=request.POST.get('expected_decision_date') or None,
            notes=request.POST.get('notes'),
        )
        lead_id = request.POST.get('lead')
        if lead_id:
            application.lead_id = lead_id
        agent_id = request.POST.get('assigned_agent')
        if agent_id:
            application.assigned_agent_id = agent_id
        application.save()

        for doc_name in DEFAULT_VISA_CHECKLIST:
            VisaDocumentChecklistItem.objects.create(application=application, document_name=doc_name)

        messages.success(request, f'Visa application for "{application.applicant_name}" created.')
        return redirect('visa_detail', pk=application.pk)

    context = {
        'active': 'visa',
        'title': 'New Visa Application',
        'category_choices': VISA_CATEGORY_CHOICES,
        'status_choices': VISA_APPLICATION_STATUS_CHOICES,
        'leads': Lead.objects.all(),
        'agents': User.objects.filter(profile__role__in=['visa_agent', 'admin', 'agency_manager']),
    }
    return render(request, 'leads/visa_form.html', context)


@login_required
def visa_detail(request, pk):
    application = get_object_or_404(VisaApplication, pk=pk)
    context = {
        'application': application,
        'checklist_items': application.checklist_items.all(),
        'active': 'visa',
        'status_choices': VISA_APPLICATION_STATUS_CHOICES,
        'doc_status_choices': VISA_DOC_STATUS_CHOICES,
    }
    return render(request, 'leads/visa_detail.html', context)


@login_required
@block_view_only
def visa_edit(request, pk):
    application = get_object_or_404(VisaApplication, pk=pk)
    if request.method == 'POST':
        application.applicant_name = request.POST.get('applicant_name')
        application.passport_number = request.POST.get('passport_number')
        application.country = request.POST.get('country')
        application.visa_category = request.POST.get('visa_category', 'tourist')
        application.application_type = request.POST.get('application_type')
        application.embassy_fee = request.POST.get('embassy_fee') or 0
        application.service_fee = request.POST.get('service_fee') or 0
        application.processing_time_days = request.POST.get('processing_time_days') or None
        application.status = request.POST.get('status', application.status)
        application.appointment_datetime = request.POST.get('appointment_datetime') or None
        application.submission_date = request.POST.get('submission_date') or None
        application.expected_decision_date = request.POST.get('expected_decision_date') or None
        application.decision_date = request.POST.get('decision_date') or None
        application.notes = request.POST.get('notes')
        lead_id = request.POST.get('lead')
        application.lead_id = lead_id if lead_id else None
        agent_id = request.POST.get('assigned_agent')
        application.assigned_agent_id = agent_id if agent_id else None
        application.save()
        messages.success(request, 'Visa application updated.')
        return redirect('visa_detail', pk=application.pk)

    context = {
        'application': application,
        'active': 'visa',
        'title': 'Edit Visa Application',
        'category_choices': VISA_CATEGORY_CHOICES,
        'status_choices': VISA_APPLICATION_STATUS_CHOICES,
        'leads': Lead.objects.all(),
        'agents': User.objects.filter(profile__role__in=['visa_agent', 'admin', 'agency_manager']),
    }
    return render(request, 'leads/visa_form.html', context)


@login_required
@block_view_only
def visa_delete(request, pk):
    application = get_object_or_404(VisaApplication, pk=pk)
    application.delete()
    messages.success(request, 'Visa application deleted.')
    return redirect('visa_list')


@login_required
@require_POST
@block_view_only
def visa_checklist_update(request, pk, item_id):
    item = get_object_or_404(VisaDocumentChecklistItem, pk=item_id, application_id=pk)
    item.status = request.POST.get('status', item.status)
    item.save()
    messages.success(request, f'"{item.document_name}" marked as {item.get_status_display()}.')
    return redirect('visa_detail', pk=pk)

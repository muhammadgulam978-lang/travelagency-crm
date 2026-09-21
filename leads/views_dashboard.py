"""
Raabta360 — Executive Dashboard & Analytics Dashboard
=====================================================
Ye module dashboard aur analytics screens ka saara data banata hai.
Purane views.py ko touch kiye bina, alag file mein rakha gaya hai taake
maintain karna asaan rahe.
"""

import calendar as _calendar
import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.shortcuts import render
from django.utils import timezone

from .models import (
    Lead, FollowUp, SalesPerson, Payment, Quotation,
    Booking, VisaApplication, Package,
    LEAD_STATUS_CHOICES, TRIP_TYPE_CHOICES,
)

# ---------------------------------------------------------------- helpers

ZERO = Decimal('0')

# Lead stage -> "maturity" bucket (requirements doc, section 21)
STAGE_ORDER = ['new', 'positive', 'quotation', 'converted', 'lost']

AI_BANDS = [
    (86, 100, 'Very Hot'),
    (71, 85, 'Hot'),
    (51, 70, 'Warm'),
    (31, 50, 'Low'),
    (0, 30, 'Cold'),
]


def _band(score):
    for lo, hi, label in AI_BANDS:
        if lo <= score <= hi:
            return label
    return 'Cold'


def _month_range(today, months=6):
    """Last N months as (year, month, 'Mon YYYY') oldest-first."""
    out = []
    for i in range(months - 1, -1, -1):
        y, m = today.year, today.month - i
        while m <= 0:
            m += 12
            y -= 1
        out.append((y, m, f"{_calendar.month_abbr[m]} {y}"))
    return out


def _pct_change(current, previous):
    """Return % change vs previous period, rounded to 1dp."""
    current = Decimal(current or 0)
    previous = Decimal(previous or 0)
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(float((current - previous) / previous * 100), 1)


def _revenue_between(start, end):
    """Total money actually received between two dates (inclusive start, exclusive end)."""
    paid = Payment.objects.filter(
        date__date__gte=start, date__date__lt=end
    ).aggregate(s=Sum('amount'))['s'] or ZERO
    booked = Booking.objects.filter(
        is_deleted=False,
        created_at__date__gte=start, created_at__date__lt=end,
    ).aggregate(s=Sum('total_received'))['s'] or ZERO
    return paid + booked


# ---------------------------------------------------------------- dashboard

@login_required
def dashboard(request):
    today = timezone.localdate()
    leads = Lead.objects.all()
    bookings = Booking.objects.filter(is_deleted=False)

    # ---------- Row 1 KPIs -------------------------------------------------
    month_start = today.replace(day=1)
    prev_month_end = month_start
    prev_month_start = (month_start - timedelta(days=1)).replace(day=1)

    total_revenue = (
        (Payment.objects.aggregate(s=Sum('amount'))['s'] or ZERO)
        + (bookings.aggregate(s=Sum('total_received'))['s'] or ZERO)
    )
    rev_this = _revenue_between(month_start, today + timedelta(days=1))
    rev_prev = _revenue_between(prev_month_start, prev_month_end)

    active_leads = leads.exclude(status__in=['lost', 'converted']).count()
    active_prev = leads.filter(created_at__date__lt=month_start).exclude(
        status__in=['lost', 'converted']).count()

    total_bookings = bookings.count()
    bookings_this = bookings.filter(created_at__date__gte=month_start).count()
    bookings_prev = bookings.filter(
        created_at__date__gte=prev_month_start, created_at__date__lt=prev_month_end).count()

    total_leads = leads.count()
    converted = leads.filter(status='converted').count()
    conversion_rate = round((converted / total_leads * 100), 1) if total_leads else 0.0

    prev_leads = leads.filter(created_at__date__lt=month_start).count()
    prev_conv = leads.filter(status='converted', created_at__date__lt=month_start).count()
    prev_rate = round((prev_conv / prev_leads * 100), 1) if prev_leads else 0.0

    kpis = [
        {
            'key': 'revenue', 'label': 'Total Revenue',
            'value': f"Rs {int(total_revenue):,}",
            'delta': _pct_change(rev_this, rev_prev), 'icon': 'revenue', 'tone': 'violet',
            'url_name': 'analytics_dashboard',
        },
        {
            'key': 'leads', 'label': 'Active Leads',
            'value': f"{active_leads:,}",
            'delta': _pct_change(active_leads, active_prev), 'icon': 'users', 'tone': 'emerald',
            'url_name': 'all_leads',
        },
        {
            'key': 'bookings', 'label': 'Bookings',
            'value': f"{total_bookings:,}",
            'delta': _pct_change(bookings_this, bookings_prev), 'icon': 'ticket', 'tone': 'sky',
            'url_name': 'booking_list',
        },
        {
            'key': 'conversion', 'label': 'Conversion Rate',
            'value': f"{conversion_rate}%",
            'delta': round(conversion_rate - prev_rate, 1), 'icon': 'target', 'tone': 'rose',
            'url_name': 'analytics_dashboard',
        },
    ]

    # ---------- Row 2: travel operations strip ----------------------------
    umrah_pax = bookings.filter(package_type='umrah').aggregate(s=Sum('no_of_pax'))['s'] or 0
    hajj_pax = bookings.filter(package_type='hajj').aggregate(s=Sum('no_of_pax'))['s'] or 0

    visa_pending = VisaApplication.objects.filter(
        status__in=['documents_required', 'submitted', 'processing', 'appointment']
    ).count()

    outstanding = ZERO
    for b in bookings.exclude(booking_status='cancelled').only(
            'package_cost_per_person', 'no_of_pax', 'visa_charges_total',
            'flight_charges_total', 'other_charges', 'total_received'):
        rem = b.balance_remaining
        if rem and rem > 0:
            outstanding += rem

    departures_today = bookings.filter(departure_date=today).exclude(
        booking_status__in=['cancelled', 'completed']).count()
    departures_upcoming = bookings.filter(
        departure_date__gt=today, departure_date__lte=today + timedelta(days=30)
    ).exclude(booking_status__in=['cancelled', 'completed']).count()

    ops_strip = [
        {'label': 'Umrah Pilgrims', 'value': f"{umrah_pax:,}", 'icon': 'kaaba', 'tone': 'violet'},
        {'label': 'Hajj Pilgrims', 'value': f"{hajj_pax:,}", 'icon': 'mosque', 'tone': 'rose'},
        {'label': 'Visa Pending', 'value': f"{visa_pending:,}", 'icon': 'passport', 'tone': 'sky'},
        {'label': 'Payments Due', 'value': f"Rs {int(outstanding):,}", 'icon': 'card', 'tone': 'amber'},
        {'label': "Today's Departures", 'value': f"{departures_today:,}", 'icon': 'plane', 'tone': 'sky'},
        {'label': 'Upcoming Departures', 'value': f"{departures_upcoming:,}", 'icon': 'calendar', 'tone': 'violet'},
    ]

    # ---------- Revenue overview chart (6 months) -------------------------
    rev_labels, rev_values = [], []
    for y, m, label in _month_range(today, 6):
        last_day = _calendar.monthrange(y, m)[1]
        start = today.replace(year=y, month=m, day=1)
        end = start + timedelta(days=last_day)
        rev_labels.append(label)
        rev_values.append(int(_revenue_between(start, end)))

    # ---------- Booking distribution donut --------------------------------
    dist_map = {'umrah': 'Umrah', 'hajj': 'Hajj', 'tour': 'International', 'other': 'Domestic'}
    dist_rows = []
    for code, label in dist_map.items():
        c = bookings.filter(package_type=code).count()
        pct = round(c / total_bookings * 100) if total_bookings else 0
        dist_rows.append({'label': label, 'count': c, 'pct': pct, 'code': code})

    # ---------- AI Lead Intelligence --------------------------------------
    hot_leads_qs = leads.exclude(status__in=['lost', 'converted']).order_by('-ai_score')[:6]
    ai_leads = []
    for l in hot_leads_qs:
        nxt = l.followups.filter(status='pending').order_by('follow_up_date').first()
        ai_leads.append({
            'obj': l,
            'band': _band(l.ai_score),
            'trip': l.get_trip_type_display() if l.trip_type else 'Travel',
            'budget': l.budget or l.quotation or 0,
            'stage': l.get_status_display(),
            'next_followup': timezone.localtime(nxt.follow_up_date) if nxt else None,
        })
    hot_count = leads.filter(ai_score__gte=71).exclude(
        status__in=['lost', 'converted']).count()

    # ---------- Upcoming departures widget --------------------------------
    upcoming_rows = bookings.filter(departure_date__gte=today).exclude(
        booking_status__in=['cancelled', 'completed']
    ).order_by('departure_date')[:5]

    # ---------- Today's follow-ups ----------------------------------------
    todays_followups = FollowUp.objects.select_related('lead').filter(
        status='pending', follow_up_date__date=today
    ).order_by('follow_up_date')[:6]
    for f in todays_followups:
        f.local_dt = timezone.localtime(f.follow_up_date)
        score = f.lead.ai_score or 0
        f.priority = 'High' if score >= 71 else ('Medium' if score >= 41 else 'Low')

    overdue_followups = FollowUp.objects.filter(
        status='pending', follow_up_date__date__lt=today).count()

    # ---------- legacy stats (purane template parts ke liye) --------------
    stats = {
        'total': total_leads,
        'new': leads.filter(status='new').count(),
        'positive': leads.filter(status='positive').count(),
        'lost': leads.filter(status='lost').count(),
        'quotation': leads.filter(status='quotation').count(),
        'convert': converted,
    }
    followup_stats = {
        'today': FollowUp.objects.filter(status='pending', follow_up_date__date=today).count(),
        'next': FollowUp.objects.filter(status='pending', follow_up_date__date__gt=today).count(),
        'pending': FollowUp.objects.filter(status='pending').count(),
        'overdue': overdue_followups,
        'done': FollowUp.objects.filter(status='done').count(),
    }

    hour = timezone.localtime().hour
    greeting = 'Morning' if hour < 12 else ('Afternoon' if hour < 17 else 'Evening')

    context = {
        'active': 'dashboard',
        'today': today,
        'greeting': greeting,
        'kpis': kpis,
        'ops_strip': ops_strip,
        'stats': stats,
        'followup_stats': followup_stats,
        'total_revenue_display': f"Rs {(float(total_revenue) / 1_000_000):.2f}M",
        'revenue_delta': _pct_change(rev_this, rev_prev),
        'rev_labels': json.dumps(rev_labels),
        'rev_values': json.dumps(rev_values),
        'dist_rows': dist_rows,
        'dist_labels': json.dumps([d['label'] for d in dist_rows]),
        'dist_values': json.dumps([d['count'] for d in dist_rows]),
        'total_bookings': total_bookings,
        'ai_leads': ai_leads,
        'hot_count': hot_count,
        'upcoming_rows': upcoming_rows,
        'todays_followups': todays_followups,
        'overdue_followups': overdue_followups,
    }
    return render(request, 'leads/dashboard.html', context)


# ---------------------------------------------------------------- analytics

@login_required
def analytics_dashboard(request):
    """Deep-dive analytics screen (funnel, sales performance, forecast, breakdowns)."""
    today = timezone.localdate()

    try:
        months = int(request.GET.get('months', 6))
    except (TypeError, ValueError):
        months = 6
    months = max(3, min(months, 12))

    period_start = (today.replace(day=1) - timedelta(days=31 * (months - 1))).replace(day=1)

    leads = Lead.objects.all()
    period_leads = leads.filter(created_at__date__gte=period_start)
    bookings = Booking.objects.filter(is_deleted=False)
    period_bookings = bookings.filter(created_at__date__gte=period_start)

    total_leads = period_leads.count()
    total_bookings = period_bookings.count()

    total_revenue = ZERO
    for b in period_bookings:
        total_revenue += b.total_received or ZERO
    total_revenue += (
        Payment.objects.filter(date__date__gte=period_start)
        .aggregate(s=Sum('amount'))['s'] or ZERO
    )

    avg_booking_value = int(total_revenue / total_bookings) if total_bookings else 0
    period_converted = period_leads.filter(status='converted').count()
    conversion_rate = round(period_converted / total_leads * 100, 1) if total_leads else 0.0

    # previous equal-length period, for the deltas
    prev_start = (period_start - timedelta(days=31 * months)).replace(day=1)
    prev_leads = leads.filter(created_at__date__gte=prev_start,
                              created_at__date__lt=period_start).count()
    prev_bookings = bookings.filter(created_at__date__gte=prev_start,
                                    created_at__date__lt=period_start).count()
    prev_converted = leads.filter(status='converted', created_at__date__gte=prev_start,
                                  created_at__date__lt=period_start).count()
    prev_revenue = _revenue_between(prev_start, period_start)
    prev_abv = int(prev_revenue / prev_bookings) if prev_bookings else 0
    prev_rate = round(prev_converted / prev_leads * 100, 1) if prev_leads else 0.0

    a_kpis = [
        {'label': 'Total Leads', 'value': f"{total_leads:,}",
         'delta': _pct_change(total_leads, prev_leads), 'icon': 'users', 'tone': 'violet'},
        {'label': 'Total Bookings', 'value': f"{total_bookings:,}",
         'delta': _pct_change(total_bookings, prev_bookings), 'icon': 'ticket', 'tone': 'sky'},
        {'label': 'Total Revenue', 'value': f"Rs {int(total_revenue):,}",
         'delta': _pct_change(total_revenue, prev_revenue), 'icon': 'revenue', 'tone': 'amber'},
        {'label': 'Average Booking Value', 'value': f"Rs {avg_booking_value:,}",
         'delta': _pct_change(avg_booking_value, prev_abv), 'icon': 'chart', 'tone': 'violet'},
        {'label': 'Conversion Rate', 'value': f"{conversion_rate}%",
         'delta': round(conversion_rate - prev_rate, 1), 'icon': 'target', 'tone': 'emerald'},
    ]

    # ---------- Lead → Booking funnel -------------------------------------
    qualified = period_leads.exclude(status__in=['new', 'lost']).count()
    quotation_sent = Quotation.objects.filter(created_at__date__gte=period_start).exclude(
        status='draft').count() or period_leads.filter(
        status__in=['quotation', 'converted']).count()
    confirmed = period_leads.filter(status='converted').count() or total_bookings

    def _p(n):
        return round(n / total_leads * 100, 1) if total_leads else 0.0

    funnel = [
        {'label': 'Total Leads', 'count': total_leads, 'pct': 100.0, 'width': 100},
        {'label': 'Qualified', 'count': qualified, 'pct': _p(qualified),
         'width': max(_p(qualified), 8)},
        {'label': 'Quotation Sent', 'count': quotation_sent, 'pct': _p(quotation_sent),
         'width': max(_p(quotation_sent), 6)},
        {'label': 'Booking Confirmed', 'count': confirmed, 'pct': _p(confirmed),
         'width': max(_p(confirmed), 4)},
    ]

    # ---------- Sales performance (revenue bars + bookings line) ----------
    perf_labels, perf_revenue, perf_bookings = [], [], []
    for y, m, label in _month_range(today, months):
        last_day = _calendar.monthrange(y, m)[1]
        start = today.replace(year=y, month=m, day=1)
        end = start + timedelta(days=last_day)
        perf_labels.append(label)
        perf_revenue.append(int(_revenue_between(start, end)))
        perf_bookings.append(
            bookings.filter(created_at__date__gte=start, created_at__date__lt=end).count()
        )

    # ---------- Simple forecast (3-month weighted moving average) ---------
    recent_rev = perf_revenue[-3:] or [0]
    recent_bk = perf_bookings[-3:] or [0]
    weights = [1, 2, 3][-len(recent_rev):]
    wsum = sum(weights) or 1
    forecast_revenue = int(sum(v * w for v, w in zip(recent_rev, weights)) / wsum)
    forecast_bookings = int(round(sum(v * w for v, w in zip(recent_bk, weights)) / wsum))
    last_rev = perf_revenue[-1] if perf_revenue else 0
    last_bk = perf_bookings[-1] if perf_bookings else 0

    # ---------- Breakdowns -------------------------------------------------
    source_rows = list(
        period_leads.values('lead_source').annotate(c=Count('id')).order_by('-c')[:6]
    )
    from .models import LEAD_SOURCE_CHOICES
    src_map = dict(LEAD_SOURCE_CHOICES)
    max_src = max([r['c'] for r in source_rows], default=1) or 1
    for r in source_rows:
        r['label'] = src_map.get(r['lead_source'], r['lead_source'] or 'Unknown')
        r['width'] = round(r['c'] / max_src * 100)

    trip_map = dict(TRIP_TYPE_CHOICES)
    trip_rows = list(
        period_leads.exclude(trip_type__isnull=True).exclude(trip_type='')
        .values('trip_type').annotate(c=Count('id')).order_by('-c')[:6]
    )
    max_trip = max([r['c'] for r in trip_rows], default=1) or 1
    for r in trip_rows:
        r['label'] = trip_map.get(r['trip_type'], r['trip_type'])
        r['width'] = round(r['c'] / max_trip * 100)

    dest_rows = list(
        period_leads.exclude(destination__isnull=True).exclude(destination='')
        .values('destination').annotate(c=Count('id')).order_by('-c')[:6]
    )
    max_dest = max([r['c'] for r in dest_rows], default=1) or 1
    for r in dest_rows:
        r['width'] = round(r['c'] / max_dest * 100)

    # ---------- Salesperson leaderboard -----------------------------------
    spo_rows = []
    for spo in SalesPerson.objects.all():
        sl = leads.filter(spo=spo)
        tot = sl.count()
        conv = sl.filter(status='converted').count()
        spo_rows.append({
            'name': spo.name,
            'total': tot,
            'positive': sl.filter(status='positive').count(),
            'quotation': sl.filter(status='quotation').count(),
            'converted': conv,
            'lost': sl.filter(status='lost').count(),
            'rate': round(conv / tot * 100, 1) if tot else 0.0,
        })
    spo_rows.sort(key=lambda r: (-r['converted'], -r['rate']))

    # ---------- Lost reasons / stage split ---------------------------------
    stage_map = dict(LEAD_STATUS_CHOICES)
    stage_rows = []
    for code, label in LEAD_STATUS_CHOICES:
        c = period_leads.filter(status=code).count()
        stage_rows.append({'code': code, 'label': label, 'count': c,
                           'pct': _p(c)})

    # ---------- Package performance ----------------------------------------
    pkg_rows = list(
        period_bookings.exclude(package_name='')
        .values('package_name', 'package_type')
        .annotate(c=Count('id'), pax=Sum('no_of_pax'), rev=Sum('total_received'))
        .order_by('-rev')[:6]
    )

    context = {
        'active': 'analytics',
        'months': months,
        'a_kpis': a_kpis,
        'funnel': funnel,
        'perf_labels': json.dumps(perf_labels),
        'perf_revenue': json.dumps(perf_revenue),
        'perf_bookings': json.dumps(perf_bookings),
        'forecast_revenue': f"Rs {forecast_revenue:,}",
        'forecast_bookings': forecast_bookings,
        'forecast_rev_delta': _pct_change(forecast_revenue, last_rev),
        'forecast_bk_delta': _pct_change(forecast_bookings, last_bk),
        'source_rows': source_rows,
        'trip_rows': trip_rows,
        'dest_rows': dest_rows,
        'spo_rows': spo_rows,
        'stage_rows': stage_rows,
        'pkg_rows': pkg_rows,
    }
    return render(request, 'leads/analytics.html', context)

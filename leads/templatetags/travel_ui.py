"""
Template helpers for the travel UI components.

Load in a template with:  {% load travel_ui %}
"""
from datetime import date, datetime

from django import template
from django.utils import timezone

register = template.Library()


# ──────────────────────────────────────────────────────────
# helpers
# ──────────────────────────────────────────────────────────

def _as_date(value):
    """Accept a date, a datetime or None and return a date (or None)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        return value.date()
    if isinstance(value, date):
        return value
    return None


@register.filter
def days_until(value):
    """
    Whole days from today until `value`.
    Negative = in the past, 0 = today. Returns None if there is no date.
    """
    target = _as_date(value)
    if target is None:
        return None
    return (target - timezone.localdate()).days


# ──────────────────────────────────────────────────────────
# departure countdown
# ──────────────────────────────────────────────────────────

@register.simple_tag
def countdown_class(value):
    """
    Pick the countdown colour band for a departure date.

        far       more than 14 days away   (calm lavender)
        soon      4-14 days away           (amber)
        imminent  1-3 days away            (red)
        today     departs today            (solid purple)
        past      already departed         (grey)
    """
    days = days_until(value)
    if days is None:
        return 'countdown-past'
    if days < 0:
        return 'countdown-past'
    if days == 0:
        return 'countdown-today'
    if days <= 3:
        return 'countdown-imminent'
    if days <= 14:
        return 'countdown-soon'
    return 'countdown-far'


@register.simple_tag
def countdown_text(value):
    """Human wording for the countdown: 'in 12 days', 'Today', '3 days ago'."""
    days = days_until(value)
    if days is None:
        return 'No date set'
    if days == 0:
        return 'Departs today'
    if days == 1:
        return 'Tomorrow'
    if days == -1:
        return 'Yesterday'
    if days > 1:
        return 'in %d days' % days
    return '%d days ago' % abs(days)


@register.simple_tag
def countdown_number(value):
    """Just the number, for the big-digit countdown box."""
    days = days_until(value)
    if days is None:
        return '—'
    return abs(days)


@register.simple_tag
def countdown_unit(value):
    """The label under/next to the big number."""
    days = days_until(value)
    if days is None:
        return ''
    if days == 0:
        return 'today'
    if days < 0:
        return 'days ago'
    return 'days to go'


# ──────────────────────────────────────────────────────────
# visa status chips (traffic light)
# ──────────────────────────────────────────────────────────

# maps VISA_APPLICATION_STATUS_CHOICES -> chip tone
_VISA_TONE = {
    'documents_required': 'chip-warning',
    'documents_received': 'chip-info',
    'submitted':          'chip-info',
    'processing':         'chip-progress',
    'appointment':        'chip-progress',
    'approved':           'chip-success',
    'rejected':           'chip-danger',
    'passport_returned':  'chip-success',
    'completed':          'chip-success',
    # Booking.visa_status uses a shorter list
    'pending':            'chip-warning',
}


@register.simple_tag
def visa_chip_class(status, expected_decision_date=None):
    """
    Chip tone for a visa application.

    The status sets the base colour, but a deadline that is close or already
    missed overrides it — an application still 'processing' two days before the
    expected decision needs to look urgent, not calm.
    """
    base = _VISA_TONE.get(status, 'chip-neutral')

    # settled statuses are never escalated
    if status in ('approved', 'rejected', 'completed', 'passport_returned'):
        return base

    days = days_until(expected_decision_date)
    if days is None:
        return base
    if days < 0:
        return 'chip-danger is-urgent'   # decision date already passed
    if days <= 3:
        return 'chip-danger'
    if days <= 7:
        return 'chip-warning'
    return base


@register.simple_tag
def visa_deadline_note(expected_decision_date):
    """Short deadline hint shown next to the visa chip."""
    days = days_until(expected_decision_date)
    if days is None:
        return ''
    if days < 0:
        return 'overdue by %d days' % abs(days)
    if days == 0:
        return 'due today'
    if days == 1:
        return 'due tomorrow'
    return 'due in %d days' % days


# ──────────────────────────────────────────────────────────
# trip progress track
# ──────────────────────────────────────────────────────────

TRIP_STAGES = ['Quoted', 'Booked', 'Visa', 'Departed']


@register.simple_tag
def trip_track(booking_status, visa_status=None, departure_date=None):
    """
    Work out how far along the Quoted -> Booked -> Visa -> Departed track a
    booking is, and return a list of {label, state} for the template to loop.

    state is one of: done, current, failed, todo
    """
    # how many stages are complete
    reached = 0                      # Quoted is always reached
    if booking_status in ('confirmed', 'completed'):
        reached = 1                  # Booked
    if visa_status in ('approved', 'passport_returned', 'completed'):
        reached = 2                  # Visa
    days = days_until(departure_date)
    if days is not None and days < 0:
        reached = 3                  # Departed
    if booking_status == 'completed':
        reached = 3

    failed_at = None
    if booking_status == 'cancelled':
        failed_at = min(reached + 1, 3)
    elif visa_status == 'rejected':
        failed_at = 2

    steps = []
    for i, label in enumerate(TRIP_STAGES):
        if failed_at is not None and i == failed_at:
            state = 'failed'
        elif i < reached:
            state = 'done'
        elif i == reached:
            state = 'done' if reached == 3 else 'current'
        else:
            state = 'todo'
        steps.append({'label': label, 'state': state})
    return steps


# ──────────────────────────────────────────────────────────
# misc
# ──────────────────────────────────────────────────────────

@register.simple_tag
def star_range(rating, out_of=5):
    """
    Return a list like [True, True, True, False, False] so a template can draw
    filled and empty stars without any arithmetic in the markup.
    """
    try:
        rating = int(rating or 0)
    except (TypeError, ValueError):
        rating = 0
    rating = max(0, min(rating, out_of))
    return [i < rating for i in range(out_of)]


@register.filter
def pax_label(booking):
    """
    Render a pax count as '2A 1C' when adults/children are known, otherwise
    fall back to the plain total ('3 pax').
    """
    adults = getattr(booking, 'adults', None)
    children = getattr(booking, 'children', None)
    if adults is None and children is None:
        total = getattr(booking, 'no_of_pax', None)
        return '%s pax' % total if total else '—'
    parts = []
    if adults:
        parts.append('%dA' % adults)
    if children:
        parts.append('%dC' % children)
    return ' '.join(parts) or '—'

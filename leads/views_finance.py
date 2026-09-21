"""
Raabta360 — Finance & Commercial Management (requirements doc, section 11)
Payment schedule -> installments -> transactions/receipts -> outstanding
balance -> aging -> refunds with approval.
"""

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .decorators import block_view_only
from .models import (
    Booking, BookingInstallment, BookingTransaction, RefundRequest,
    PAYMENT_METHOD_CHOICES, INSTALLMENT_STATUS_CHOICES, REFUND_STATUS_CHOICES,
)

_INPUT = {'class': 'form-control'}


class BookingInstallmentForm(forms.ModelForm):
    class Meta:
        model = BookingInstallment
        fields = ['label', 'amount', 'due_date', 'notes']
        widgets = {
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.TextInput(attrs=_INPUT),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('label', 'amount'):
            self.fields[name].widget.attrs.setdefault('class', 'form-control')


class BookingTransactionForm(forms.ModelForm):
    class Meta:
        model = BookingTransaction
        fields = ['installment', 'amount', 'payment_method', 'reference_number',
                  'transaction_date', 'notes']
        widgets = {
            'transaction_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.TextInput(attrs=_INPUT),
        }

    def __init__(self, *args, booking=None, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('amount', 'payment_method', 'reference_number', 'installment'):
            self.fields[name].widget.attrs.setdefault('class', 'form-control')
        if booking is not None:
            self.fields['installment'].queryset = booking.installments.exclude(status='paid')
        self.fields['installment'].required = False


class RefundRequestForm(forms.ModelForm):
    class Meta:
        model = RefundRequest
        fields = ['amount', 'reason']
        widgets = {'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['amount'].widget.attrs.setdefault('class', 'form-control')


# ---------------------------------------------------------------- receivables

@login_required
def receivables_list(request):
    """
    Outstanding balances across all active bookings, with payment aging
    buckets (11.1 Payment aging).
    """
    bookings = Booking.objects.filter(is_deleted=False).exclude(
        booking_status='cancelled').select_related('client', 'company')

    today = timezone.localdate()
    rows = []
    aging_buckets = {'current': 0, '1_30': 0, '31_60': 0, '61_90': 0, '90_plus': 0}

    for b in bookings:
        outstanding = b.outstanding_balance
        if outstanding <= 0:
            continue
        due = b.next_due_installment
        days_late = due.days_overdue if due else 0

        if days_late <= 0:
            bucket = 'current'
        elif days_late <= 30:
            bucket = '1_30'
        elif days_late <= 60:
            bucket = '31_60'
        elif days_late <= 90:
            bucket = '61_90'
        else:
            bucket = '90_plus'
        aging_buckets[bucket] += float(outstanding)

        rows.append({
            'booking': b,
            'outstanding': outstanding,
            'due': due,
            'days_late': days_late,
            'bucket': bucket,
            'status': b.payment_status,
        })

    q = request.GET.get('q')
    if q:
        rows = [r for r in rows if q.lower() in r['booking'].client_or_company_name.lower()]

    bucket_filter = request.GET.get('bucket')
    if bucket_filter:
        rows = [r for r in rows if r['bucket'] == bucket_filter]

    rows.sort(key=lambda r: -r['days_late'])
    total_outstanding = sum(r['outstanding'] for r in rows)

    return render(request, 'leads/receivables_list.html', {
        'rows': rows,
        'active': 'receivables',
        'total_outstanding': total_outstanding,
        'aging_buckets': aging_buckets,
        'today': today,
    })


# ---------------------------------------------------------------- invoice / booking finance detail

@login_required
def booking_finance_detail(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    installments = booking.installments.all()
    transactions = booking.transactions.select_related('installment', 'created_by').all()
    refunds = booking.refund_requests.select_related('requested_by', 'approved_by').all()

    return render(request, 'leads/booking_finance_detail.html', {
        'booking': booking,
        'installments': installments,
        'transactions': transactions,
        'refunds': refunds,
        'installment_form': BookingInstallmentForm(),
        'transaction_form': BookingTransactionForm(booking=booking),
        'refund_form': RefundRequestForm(),
        'active': 'receivables',
        'today': timezone.localdate(),
    })


@login_required
@block_view_only
def booking_installment_add(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == 'POST':
        form = BookingInstallmentForm(request.POST)
        if form.is_valid():
            inst = form.save(commit=False)
            inst.booking = booking
            inst.save()
            messages.success(request, f'Installment "{inst.label}" added.')
        else:
            messages.error(request, 'Could not add installment — check the fields.')
    return redirect('booking_finance_detail', pk=booking.pk)


@login_required
@block_view_only
def booking_transaction_add(request, pk):
    """Record a receipt (payment) against a booking — generates a receipt number."""
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == 'POST':
        form = BookingTransactionForm(request.POST, booking=booking)
        if form.is_valid():
            txn = form.save(commit=False)
            txn.booking = booking
            txn.transaction_type = 'payment'
            txn.created_by = request.user
            txn.save()
            # keep the legacy total_received in sync for anything still reading it
            booking.total_received = booking.amount_collected
            booking.save(update_fields=['total_received'])
            messages.success(request, f'Payment recorded — receipt {txn.receipt_number}.')
        else:
            messages.error(request, 'Could not record the payment — check the fields.')
    return redirect('booking_finance_detail', pk=booking.pk)


@login_required
def receipt_view(request, pk):
    """Printable receipt for a single transaction."""
    txn = get_object_or_404(BookingTransaction, pk=pk)
    return render(request, 'leads/receipt_view.html', {'txn': txn, 'booking': txn.booking})


# ---------------------------------------------------------------- refunds

@login_required
@block_view_only
def refund_request_create(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == 'POST':
        form = RefundRequestForm(request.POST)
        if form.is_valid():
            r = form.save(commit=False)
            r.booking = booking
            r.requested_by = request.user
            r.save()
            messages.success(request, 'Refund request submitted for approval.')
        else:
            messages.error(request, 'Could not submit the refund request.')
    return redirect('booking_finance_detail', pk=booking.pk)


@login_required
def refund_list(request):
    """Pending / decided refund requests — approval queue (11.3)."""
    refunds = RefundRequest.objects.select_related('booking', 'requested_by', 'approved_by').all()
    status = request.GET.get('status', 'pending')
    if status:
        refunds = refunds.filter(status=status)
    return render(request, 'leads/refund_list.html', {
        'refunds': refunds,
        'active': 'receivables',
        'status_choices': REFUND_STATUS_CHOICES,
        'current_status': status,
        'pending_count': RefundRequest.objects.filter(status='pending').count(),
    })


@login_required
@block_view_only
def refund_approve(request, pk):
    """CEO/Finance-only approval — creates the actual refund transaction."""
    refund = get_object_or_404(RefundRequest, pk=pk)
    if refund.status != 'pending':
        messages.info(request, 'This refund has already been decided.')
        return redirect('refund_list')

    if not (request.user.is_superuser or getattr(
            getattr(request.user, 'custom_permissions', None), 'finance', 'none') == 'full'):
        messages.error(request, 'Only Finance/CEO can approve refunds.')
        return redirect('refund_list')

    txn = refund.approve_and_process(request.user)
    booking = refund.booking
    booking.total_received = booking.amount_collected
    booking.save(update_fields=['total_received'])
    messages.success(request, f'Refund approved — {txn.receipt_number} issued.')
    return redirect('refund_list')


@login_required
@block_view_only
def refund_reject(request, pk):
    refund = get_object_or_404(RefundRequest, pk=pk)
    if refund.status == 'pending':
        refund.reject(request.user, notes=request.POST.get('notes', ''))
        messages.success(request, 'Refund request rejected.')
    return redirect('refund_list')

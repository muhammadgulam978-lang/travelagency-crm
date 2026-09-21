from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings



class SalesPerson(models.Model):
    """SPO - Sales Person Officer assigned to leads,"""
    name = models.CharField(max_length=100)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null = True, blank = True)

    def __str__(self):
        return self.name

ROLE_CHOICES = [
    ('admin', 'Super Admin'),
    ('agency_manager', 'Agency Manager'),
    ('sales_executive', 'Sales Agent'),
    ('visa_agent', 'Visa Agent'),
    ('operations', 'Operations Staff'),
    ('finance', 'Accountant'),
    ('marketing', 'Marketing User'),
    ('ceo', 'CEO'),
]


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='sales_executive')
    phone = models.CharField(max_length=30, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    email_account_key = models.CharField(max_length=50, default='default', blank=True)
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"    


class UserPermissions(models.Model):
    """
    Custom per-user permissions.
    Each section can be: 'full', 'view', or 'none'
    This overrides role-based permissions when set.
    """
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='custom_permissions'
    )

    # CRM Sections
    dashboard = models.CharField(max_length=10, default='full')
    leads = models.CharField(max_length=10, default='none')
    contacts = models.CharField(max_length=10, default='none')
    pipeline = models.CharField(max_length=10, default='none')
    quotations = models.CharField(max_length=10, default='none')
    meetings = models.CharField(max_length=10, default='none')
    tasks = models.CharField(max_length=10, default='none')
    payments = models.CharField(max_length=10, default='none')
    followups = models.CharField(max_length=10, default='none')
    communications = models.CharField(max_length=10, default='none')
    emails = models.CharField(max_length=10, default='none')
    crm_chatbot = models.CharField(max_length=10, default='none')     # CRM Assistant
    sales_chatbot = models.CharField(max_length=10, default='none')
    activity = models.CharField(max_length=10, default='none')
    reports = models.CharField(max_length=10, default='none')
    documents = models.CharField(max_length=10, default='none')
    contracts = models.CharField(max_length=10, default='none')
    booking = models.CharField(max_length=10, default='none')
    packages = models.CharField(max_length=10, default='none')
    visa = models.CharField(max_length=10, default='none')
    salespersons = models.CharField(max_length=10, default='none')
    users = models.CharField(max_length=10, default='none')
    ceo_dashboard = models.CharField(max_length=10, default='none')
    whatsapp = models.CharField(max_length=10, default='none')
    hotels = models.CharField(max_length=10, default='none')
    transportation = models.CharField(max_length=10, default='none')
    itineraries = models.CharField(max_length=10, default='none')
    suppliers = models.CharField(max_length=10, default='none')
    corporate = models.CharField(max_length=10, default='none')
    bulk_email = models.CharField(max_length=10, default='none')
    reviews = models.CharField(max_length=10, default='none')

    updated_at = models.DateTimeField(auto_now=True)

    # permission choices
    PERMISSION_CHOICES = [
        ('full', 'Full Access'),
        ('view', 'View Only'),
        ('none', 'No Access'),
    ]

    ALL_SECTIONS = [
        'dashboard', 'leads', 'contacts', 'pipeline', 'quotations',
        'meetings', 'tasks', 'payments', 'followups',
        'communications', 'emails', 'activity', 'reports', 'documents',
        'contracts', 'booking', 'packages', 'visa', 'salespersons', 'users', 'ceo_dashboard', 'whatsapp',
        'crm_chatbot', 'sales_chatbot',
        'hotels', 'transportation', 'itineraries', 'suppliers', 'corporate', 'bulk_email', 'reviews',
    ]

    def get_section_permission(self, section: str) -> str:
        return getattr(self, section, 'none')

    def has_access(self, section: str) -> bool:
        return self.get_section_permission(section) in ['full', 'view']

    def is_view_only(self, section: str) -> bool:
        return self.get_section_permission(section) == 'view'

    def has_full_access(self, section: str) -> bool:
        return self.get_section_permission(section) == 'full'

    def __str__(self):
        return f"Permissions for {self.user.username}"


LEAD_SOURCE_CHOICES = [
    ('advertisement', 'Advertisement'),
    ('landline', 'Landline'),
    ('direct_call', 'Direct Call'),
    ('facebook', 'Facebook'),
    ('whatsapp', 'Whatsapp'),
    ('website', 'Website'),
    ('personal_reference', 'Personal Reference'),
    ('client_reference', 'Client Reference'),
    ('staff_reference', 'Staff Reference'),
    ('email', 'Email'),
    ('walkin', 'Walkin'),
    ('instagram', 'Instagram'),
    ('google', 'Google'),
]

TRIP_TYPE_CHOICES = [
    ('package_tour', 'Package Tour'),
    ('group_tour', 'Group Tour'),
    ('private_tour', 'Private / Customized Tour'),
    ('honeymoon', 'Honeymoon Tour'),
    ('corporate', 'Corporate Travel'),
    ('umrah', 'Umrah'),
    ('hajj', 'Hajj'),
    ('visa_only', 'Visa Only'),
    ('air_ticket_only', 'Air Ticket Only'),
    ('hotel_only', 'Hotel Only'),
    ('transport_only', 'Transportation Only'),
    ('excursion', 'Excursion / Activity'),
    ('other', 'Other'),
]

LEAD_STATUS_CHOICES = [
    ('new', 'New'),
    ('contacted', 'Contacted'),
    ('qualified', 'Qualified'),
    ('positive', 'Positive'),
    ('quotation', 'Quotation Sent'),
    ('followup', 'Follow-up'),
    ('booking_pending', 'Booking Pending'),
    ('converted', 'Converted'),
    ('lost', 'Lost'),
]

class Lead(models.Model):
    lead_source    = models.CharField(max_length=30, choices=LEAD_SOURCE_CHOICES, default='advertisement')
    name           = models.CharField(max_length=150)
    contact_number = models.CharField(max_length=30)
    email          = models.EmailField(blank=True, null=True)
    country        = models.CharField(max_length=100, blank=True, null=True)
    city           = models.CharField(max_length=100, blank=True, null=True)
    address        = models.CharField(max_length=225, blank=True, null=True)
    quotation      = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    detail         = models.TextField(blank=True, null=True)

    # Travel-specific fields
    trip_type        = models.CharField(max_length=30, choices=TRIP_TYPE_CHOICES, blank=True, null=True)
    destination       = models.CharField(max_length=150, blank=True, null=True)
    travel_start_date = models.DateField(blank=True, null=True)
    travel_end_date   = models.DateField(blank=True, null=True)
    adults            = models.PositiveIntegerField(default=1)
    children           = models.PositiveIntegerField(default=0)
    budget            = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    status         = models.CharField(max_length=20, choices=LEAD_STATUS_CHOICES, default='new')
    spo            = models.ForeignKey(SalesPerson, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    created_at     = models.DateTimeField(default=timezone.now)
    updated_at     = models.DateTimeField(auto_now=True)
    is_duplicate   = models.BooleanField(default=False)
    duplicate_of   = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='duplicates'
    )
    ai_score       = models.IntegerField(default=0, help_text='AI lead score 0-100')
    ai_score_reason = models.TextField(blank=True, null=True)
    ai_score_updated = models.DateTimeField(blank=True, null=True)
    closing_probability = models.IntegerField(default=0)
    closing_probability_updated = models.DateTimeField(blank=True, null=True)
    closing_probability_reason = models.TextField(blank=True, null=True)
    churn_risk = models.CharField(max_length=10, blank=True, null=True)
    churn_risk_reason = models.TextField(blank=True, null=True)
    churn_risk_updated = models.DateTimeField(blank=True, null=True)
    lifetime_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    lifetime_value_updated = models.DateTimeField(blank=True, null=True)
    lifetime_value_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    class Meta:
        ordering = ['-created_at']

INDUSTRY_CHOICES = [
    ('technology', 'Technology'),
    ('finance', 'Finance'),
    ('healthcare', 'Healthcare'),
    ('education', 'Education'),
    ('retail', 'Retail'),
    ('manufacturing', 'Manufacturing'),
    ('real_estate', 'Real Estate'),
    ('construction', 'Construction'),
    ('marketing', 'Marketing'),
    ('other', 'Other'),
]


class Company(models.Model):
    name = models.CharField(max_length=200)
    industry = models.CharField(max_length=30, choices=INDUSTRY_CHOICES, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Companies'


class Contact(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    job_title = models.CharField(max_length=100, blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='contacts')
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='contacts')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name or ''}".strip()

    def get_full_name(self):
        return f"{self.first_name} {self.last_name or ''}".strip()

    class Meta:
        ordering = ['first_name']

OPPORTUNITY_STAGE_CHOICES = [
    ('new', 'New'),
    ('contacted', 'Contacted'),
    ('qualified', 'Qualified'),
    ('proposal', 'Proposal Sent'),
    ('negotiation', 'Negotiation'),
    ('won', 'Won'),
    ('lost', 'Lost'),
]

PRIORITY_CHOICES = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High')
]

class Opportunity(models.Model):
    title               = models.CharField(max_length=200)
    lead                = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='opportunities')
    contact             = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='opportunities')
    company             = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='opportunities')
    assigned_to         = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='opportunities')
    stage               = models.CharField(max_length=20, choices=OPPORTUNITY_STAGE_CHOICES, default='new')
    priority            = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    value               = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    probability         = models.IntegerField(default=0, help_text='Win probability 0-100%')
    expected_close_date = models.DateField(blank=True, null=True)
    description         = models.TextField(blank=True, null=True)
    lost_reason         = models.TextField(blank=True, null=True)
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Opportunities'

QUOTATION_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('sent', 'Sent'),
    ('viewed', 'Viewed'),
    ('approved', 'Accepted'),
    ('rejected', 'Rejected'),
    ('expired', 'Expired'),
]


class Quotation(models.Model):
    opportunity = models.ForeignKey(Opportunity, on_delete=models.SET_NULL, null=True, blank=True, related_name='quotations')
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='quotations')
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='quotations')
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='quotations')
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=QUOTATION_STATUS_CHOICES, default='draft')
    valid_until = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    terms = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='quotations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def total_amount(self):
        return sum(item.total_price() for item in self.items.all())

    class Meta:
        ordering = ['-created_at']


class QuotationItem(models.Model):
    ITEM_TYPE_CHOICES = [
        ('flight', 'Flight'),
        ('hotel', 'Hotel'),
        ('transport', 'Transport'),
        ('visa', 'Visa'),
        ('activity', 'Activity / Sightseeing'),
        ('insurance', 'Insurance'),
        ('service_charge', 'Service Charge'),
        ('other', 'Other'),
    ]
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='items')
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES, default='other')
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def total_price(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return self.description

MEETING_STATUS_CHOICES = [
    ('scheduled', 'Scheduled'),
    ('re_scheduled', 'Re-Scheduled'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
    ('no_show', 'No Show'),
]

MEETING_TYPE_CHOICES = [
    ('call', 'Phone Call'),
    ('video', 'Video Call'),
    ('in_person', 'In Person'),
    ('demo', 'Demo'),
    ('follow_up', 'Follow Up'),
]

GENERAL_TASK_STATUS_CHOICES = [
    ('todo', 'To Do'),
    ('in_progress', 'In Progress'),
    ('done', 'Done'),
]

GENERAL_TASK_PRIORITY_CHOICES = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
]


class Meeting(models.Model):
    title = models.CharField(max_length=200)
    meeting_type = models.CharField(max_length=20, choices=MEETING_TYPE_CHOICES, default='call')
    status = models.CharField(max_length=20, choices=MEETING_STATUS_CHOICES, default='scheduled')
    scheduled_at = models.DateTimeField()
    duration_minutes = models.IntegerField(default=30)
    location = models.CharField(max_length=255, blank=True, null=True)
    agenda = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    action_items = models.TextField(blank=True, null=True)
    lead = models.ForeignKey(
        Lead, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='meetings'
    )
    opportunity = models.ForeignKey(
        Opportunity, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='meetings'
    )
    company = models.ForeignKey(
        Company, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='meetings'
    )
    contact = models.ForeignKey(
        Contact, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='meetings'
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='created_meetings'
    )
    attendees = models.ManyToManyField(
        User, blank=True, related_name='meetings'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    ai_summary = models.TextField(blank=True, null=True)
    ai_summary_updated = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} — {self.scheduled_at:%d %b %Y %H:%M}"

    class Meta:
        ordering = ['-scheduled_at']


class GeneralTask(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='general_tasks'
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='created_tasks'
    )
    status = models.CharField(
        max_length=15,
        choices=GENERAL_TASK_STATUS_CHOICES,
        default='todo'
    )
    priority = models.CharField(
        max_length=10,
        choices=GENERAL_TASK_PRIORITY_CHOICES,
        default='medium'
    )
    due_date = models.DateField(blank=True, null=True)
    lead = models.ForeignKey(
        Lead, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='general_tasks'
    )
    opportunity = models.ForeignKey(
        Opportunity, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='general_tasks'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['due_date', '-created_at']

COMMUNICATION_TYPE_CHOICES = [
    ('email', 'Email'),
    ('call', 'Phone Call'),
    ('whatsapp', 'WhatsApp'),
    ('sms', 'SMS'),
    ('note', 'Internal Note'),
    ('meeting_note', 'Meeting Note'),
]

COMMUNICATION_DIRECTION_CHOICES = [
    ('inbound', 'Inbound'),
    ('outbound', 'Outbound'),
    ('internal', 'Internal'),
]


class CommunicationLog(models.Model):
    comm_type = models.CharField(max_length=20, choices=COMMUNICATION_TYPE_CHOICES, default='note')
    direction = models.CharField(max_length=10, choices=COMMUNICATION_DIRECTION_CHOICES, default='outbound')
    subject = models.CharField(max_length=255, blank=True, null=True)
    body = models.TextField()
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='communications'
    )
    lead = models.ForeignKey(
        Lead, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='communications'
    )
    opportunity = models.ForeignKey(
        Opportunity, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='communications'
    )
    contact = models.ForeignKey(
        Contact, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='communications'
    )
    company = models.ForeignKey(
        Company, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='communications'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_comm_type_display()} — {self.created_at:%d %b %Y}"

    class Meta:
        ordering = ['-created_at']

class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('deleted', 'Deleted'),
        ('status_changed', 'Status Changed'),
        ('assigned', 'Assigned'),
        ('commented', 'Commented'),
        ('payment', 'Payment Recorded'),
        ('converted', 'Converted'),
        ('login', 'Logged In'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='activity_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    entity_type = models.CharField(max_length=50)
    entity_id = models.IntegerField(null=True, blank=True)
    entity_name = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} — {self.action} — {self.entity_type}"

    class Meta:
        ordering = ['-created_at']

class FollowUp(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('done', 'Done'),
    ]
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='followups')
    follow_up_date= models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Followup for {self.lead.name} on {self.follow_up_date:%Y-%m-%d}"
    
    class Meta:
        ordering = ['follow_up_date']

PAYMENT_TYPE_CHOICES = [
    ('advance', 'Advance'),
    ('full', 'Full'),
]

class Payment(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='payments')
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    notes = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.get_payment_type_display()} - {self.amount} for {self.lead.name}"

    class Meta:
        ordering = ['-date']

class ScheduledPayment(models.Model):
    """A payment plan for a lead broken into installments."""
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='scheduled_payments')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Payment Plan for {self.lead.name} - Total: {self.total_amount}"

    def amount_paid(self):
        return sum(i.amount for i in self.installments.filter(is_paid=True))

    def amount_remaining(self):
        return self.total_amount - self.amount_paid()

    def next_due(self):
        return self.installments.filter(is_paid=False).order_by('due_date').first()
    
    class Meta:
        ordering = ['-created_at']


class Installment(models.Model):
    schedule  = models.ForeignKey(ScheduledPayment, on_delete=models.CASCADE, related_name='installments')
    amount    = models.DecimalField(max_digits=12, decimal_places=2)
    due_date  = models.DateField()
    is_paid   = models.BooleanField(default=False)
    paid_date = models.DateField(blank=True, null=True)
    notes     = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Installment of {self.amount} due {self.due_date}"
    
    class Meta:
        ordering = ['due_date']

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

# ── Auto-create UserProfile ────────────────────────────────
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
        UserPermissions.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


# ── Activity Log helpers ───────────────────────────────────
def log_activity(user, action, entity_type, entity_id, entity_name, description):
    ActivityLog.objects.create(
        user=user,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        description=description,
    )

DOCUMENT_TYPE_CHOICES = [
    ('proposal', 'Proposal'),
    ('contract', 'Contract'),
    ('invoice', 'Invoice'),
    ('requirement', 'Requirement Document'),
    ('design', 'Design File'),
    ('report', 'Report'),
    ('other', 'Other'),
]


class Document(models.Model):
    title = models.CharField(max_length=200)
    doc_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES, default='other')
    file = models.FileField(upload_to='documents/%Y/%m/')
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='documents'
    )
    lead = models.ForeignKey(
        Lead, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='documents'
    )
    opportunity = models.ForeignKey(
        Opportunity, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='documents'
    )
    quotation = models.ForeignKey(
        Quotation, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='documents'
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def filename(self):
        import os
        return os.path.basename(self.file.name)

    def filesize(self):
        try:
            size = self.file.size
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size // 1024} KB"
            else:
                return f"{size // (1024 * 1024)} MB"
        except Exception:
            return "Unknown"

    class Meta:
        ordering = ['-created_at']

CONTRACT_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('sent', 'Sent to Client'),
    ('signed', 'Signed'),
    ('active', 'Active'),
    ('expired', 'Expired'),
    ('cancelled', 'Cancelled'),
]


class Contract(models.Model):
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=CONTRACT_STATUS_CHOICES, default='draft')
    opportunity = models.ForeignKey(
        Opportunity, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='contracts'
    )
    quotation = models.ForeignKey(
        Quotation, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='contracts'
    )
    company = models.ForeignKey(
        Company, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='contracts'
    )
    contact = models.ForeignKey(
        Contact, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='contracts'
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='contracts'
    )
    value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    signed_date = models.DateField(blank=True, null=True)
    terms = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    signed_file = models.FileField(
        upload_to='contracts/%Y/%m/',
        blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    class Meta:
        ordering = ['-created_at']


class Proposal(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generated', 'AI Generated'),
        ('approved', 'Approved'),
        ('sent', 'Sent to Client'),
    ]

    lead = models.ForeignKey(
        Lead, on_delete=models.CASCADE,
        related_name='proposals', null=True, blank=True
    )
    title = models.CharField(max_length=200, default='Business Proposal')
    uploaded_pdf = models.FileField(
        upload_to='proposals/pdfs/%Y/%m/',
        blank=True, null=True
    )
    pdf_extracted_text = models.TextField(blank=True, null=True)
    manual_notes = models.TextField(blank=True, null=True)
    generated_proposal = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='draft'
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='proposals'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} — {self.lead.name if self.lead else 'No Lead'}"

    class Meta:
        ordering = ['-created_at']


class Notification(models.Model):
    NOTIF_TYPE_CHOICES = [
        ('followup_due', 'Follow Up Due'),
        ('meeting_today', 'Meeting Today'),
        ('task_overdue',  'Task Overdue'),
        ('lead_assigned', 'Lead Assigned'),
        ('payment_received', 'Payment_received'),
        ('contract_signed', 'Contract Update'),
        ('general', 'General'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='notifications'
    )
    notif_type = models.CharField(max_length=30, choices=NOTIF_TYPE_CHOICES, default='general')
    title      = models.CharField(max_length=200)
    message    = models.TextField()
    link       = models.CharField(max_length=255, blank=True, null=True)
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    class Meta:
        ordering = ['-created_at']


class AssistantPermission(models.Model):
    ACCESS_CHOICES = [
        ('none', 'No Access'),
        ('view', 'View Only'),
        ('full', 'Full Access'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='assistant_permission')
    crm_assistant = models.CharField(max_length=10, choices=ACCESS_CHOICES, default='none')
    sales_assistant = models.CharField(max_length=10, choices=ACCESS_CHOICES, default='none')

    def can_query(self, assistant_type):
        level = self.crm_assistant if assistant_type == 'crm' else self.sales_assistant
        return level in ('view', 'full')

    def can_act(self, assistant_type):
        level = self.crm_assistant if assistant_type == 'crm' else self.sales_assistant
        return level == 'full'


class AssistantConversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assistant_conversations')
    assistant_type = models.CharField(max_length=10, choices=[('crm', 'CRM'), ('sales', 'Sales')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AssistantMessage(models.Model):
    ROLE_CHOICES = [('user', 'User'), ('assistant', 'Assistant')]
    conversation = models.ForeignKey(AssistantConversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    tool_used = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class AssistantAuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    assistant_type = models.CharField(max_length=10)
    query = models.TextField()
    action_executed = models.CharField(max_length=100, blank=True, null=True)
    success = models.BooleanField(default=True)
    response = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']


# ── Lead signals ───────────────────────────────────────────
@receiver(post_save, sender=Lead)
def log_lead_save(sender, instance, created, **kwargs):
    action = 'created' if created else 'updated'
    description = f'Lead "{instance.name}" was {action}.'
    log_activity(None, action, 'Lead', instance.pk, instance.name, description)


# ── Opportunity signals ────────────────────────────────────
@receiver(post_save, sender=Opportunity)
def log_opportunity_save(sender, instance, created, **kwargs):
    action = 'created' if created else 'updated'
    description = f'Opportunity "{instance.title}" was {action} — Stage: {instance.get_stage_display()}.'
    log_activity(None, action, 'Opportunity', instance.pk, instance.title, description)


# ── Payment signals ────────────────────────────────────────
@receiver(post_save, sender=Payment)
def log_payment_save(sender, instance, created, **kwargs):
    if created:
        description = f'{instance.get_payment_type_display()} payment of {instance.amount} recorded for "{instance.lead.name}".'
        log_activity(None, 'payment', 'Payment', instance.pk, str(instance.amount), description)


# ── FollowUp signals ───────────────────────────────────────
@receiver(post_save, sender=FollowUp)
def log_followup_save(sender, instance, created, **kwargs):
    if created:
        description = f'Follow-up scheduled for lead "{instance.lead.name}" on {instance.follow_up_date:%d %b %Y}.'
        log_activity(None, 'created', 'FollowUp', instance.pk, instance.lead.name, description)


# ── Meeting signals ────────────────────────────────────────
@receiver(post_save, sender=Meeting)
def log_meeting_save(sender, instance, created, **kwargs):
    if created:
        try:
            scheduled = instance.scheduled_at.strftime('%d %b %Y %H:%M')
        except Exception:
            scheduled = str(instance.scheduled_at)
        description = f'Meeting "{instance.title}" scheduled for {scheduled}.'
        log_activity(None, 'created', 'Meeting', instance.pk, instance.title, description)


class EmailLog(models.Model):
    lead = models.ForeignKey(
        'Lead',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='emails'
    )
    sent_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    to_email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=20, default='sent')  # sent / failed
    created_at = models.DateTimeField(auto_now_add=True)
    # --- naye fields ---
    from_email = models.CharField(max_length=255, blank=True, null=True)
    direction = models.CharField(
        max_length=10,
        choices=[('outbound', 'Outbound'), ('inbound', 'Inbound')],
        default='outbound',
    )
    account_key = models.CharField(max_length=50, default='default', blank=True)
    def __str__(self):
        return f"{self.subject} → {self.to_email}"
    
    
    
    


class CallLog(models.Model):
    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('ringing', 'Ringing'),
        ('in-progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('no-answer', 'No Answer'),
        ('rejected', 'Rejected'),
    ]
    CHANNEL_CHOICES = [
        ('phone', 'Phone (Twilio)'),
        ('whatsapp', 'WhatsApp (Meta Calling API)'),
    ]

    lead = models.ForeignKey('Lead', on_delete=models.CASCADE, related_name='calls')
    caller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    call_sid = models.CharField(max_length=150, blank=True, null=True)  # Twilio CallSid OR Meta call_id
    to_number = models.CharField(max_length=20)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='phone')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated')
    duration = models.IntegerField(default=0)  # seconds
    recording_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.channel} call to {self.to_number} ({self.status})"


class CallSchedule(models.Model):
    lead = models.ForeignKey('Lead', on_delete=models.CASCADE, related_name='scheduled_calls')
    scheduled_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    scheduled_time = models.DateTimeField()
    note = models.TextField(blank=True)
    google_event_id = models.CharField(max_length=255, blank=True, null=True)
    reminder_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_time']

    def __str__(self):
        return f"Call with {self.lead} at {self.scheduled_time}"


class GoogleCredential(models.Model):
    """Stores OAuth tokens per CRM user for Google Calendar access."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    access_token = models.TextField()
    refresh_token = models.TextField()
    token_expiry = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Google credentials for {self.user}"


# ============================================================
# BOOKING MODULE
# ============================================================

BOOKING_PACKAGE_TYPE_CHOICES = [
    ('umrah', 'Umrah'),
    ('hajj', 'Hajj'),
    ('tour', 'Tour'),
    ('other', 'Other'),
]

BOOKING_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('confirmed', 'Confirmed'),
    ('cancelled', 'Cancelled'),
    ('completed', 'Completed'),
]

BOOKING_FOR_CHOICES = [
    ('client', 'Client'),
    ('company', 'Company'),
]

ROOM_TYPE_CHOICES = [
    ('single', 'Single'),
    ('double', 'Double'),
    ('triple', 'Triple'),
    ('quad', 'Quad'),
    ('sharing', 'Sharing'),
]

TRANSPORT_TYPE_CHOICES = [
    ('private_car', 'Private Car'),
    ('coaster', 'Coaster'),
    ('bus', 'Bus'),
    ('van', 'Van'),
]

BOOKING_VISA_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('submitted', 'Submitted'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
]


class Booking(models.Model):
    # Package tab
    package_type = models.CharField(max_length=20, choices=BOOKING_PACKAGE_TYPE_CHOICES, default='umrah')
    year = models.PositiveIntegerField(default=2026)
    package_name = models.CharField(max_length=200, blank=True)
    booking_status = models.CharField(max_length=20, choices=BOOKING_STATUS_CHOICES, default='pending')

    # Booking Details tab
    booking_for = models.CharField(max_length=10, choices=BOOKING_FOR_CHOICES, default='client')
    client = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    no_of_pax = models.PositiveIntegerField(default=1)
    care_of = models.CharField(max_length=150, blank=True)
    passport_number = models.CharField(max_length=50, blank=True)
    cnic_number = models.CharField(max_length=50, blank=True)
    phone_number = models.CharField(max_length=30, blank=True)
    emergency_phone = models.CharField(max_length=30, blank=True)
    voucher_number = models.CharField(max_length=50, blank=True)
    card_number = models.CharField(max_length=50, blank=True)

    # Flight tab
    departure_date = models.DateField(null=True, blank=True)
    departure_flight_no = models.CharField(max_length=30, blank=True)
    departure_time = models.TimeField(null=True, blank=True)
    departure_airline = models.CharField(max_length=100, blank=True)
    departure_pnr = models.CharField(max_length=50, blank=True)
    arrival_date = models.DateField(null=True, blank=True)
    arrival_flight_no = models.CharField(max_length=30, blank=True)
    arrival_time = models.TimeField(null=True, blank=True)
    arrival_airline = models.CharField(max_length=100, blank=True)
    arrival_pnr = models.CharField(max_length=50, blank=True)

    # Costing tab
    package_cost_per_person = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    visa_charges_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    flight_charges_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_received = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    @property
    def total_amount(self):
        return (self.package_cost_per_person * self.no_of_pax) + self.visa_charges_total + self.flight_charges_total + self.other_charges

    @property
    def balance_remaining(self):
        return self.total_amount - self.total_received

    @property
    def amount_collected(self):
        """Prefers the real transaction ledger; falls back to the legacy total_received field."""
        if self.transactions.exists():
            paid = self.transactions.filter(transaction_type='payment').aggregate(
                s=models.Sum('amount'))['s'] or 0
            refunded = self.transactions.filter(transaction_type='refund').aggregate(
                s=models.Sum('amount'))['s'] or 0
            return paid - refunded
        return self.total_received

    @property
    def outstanding_balance(self):
        return self.total_amount - self.amount_collected

    @property
    def payment_status(self):
        outstanding = self.outstanding_balance
        if outstanding <= 0:
            return 'paid'
        overdue = self.installments.filter(status='overdue').exists() or any(
            i.days_overdue > 0 for i in self.installments.filter(status__in=['pending', 'partial'])
        )
        if overdue:
            return 'overdue'
        if self.amount_collected > 0:
            return 'partial'
        return 'unpaid'

    @property
    def next_due_installment(self):
        return self.installments.exclude(status='paid').order_by('due_date').first()

    @property
    def client_or_company_name(self):
        if self.booking_for == 'company' and self.company_id:
            return self.company.name
        if self.client_id:
            return self.client.get_full_name()
        return '—'

    def __str__(self):
        return f"{self.client_or_company_name} - {self.package_name or self.get_package_type_display()}"


class BookingPerson(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='persons')
    is_main = models.BooleanField(default=False)
    client = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=150, blank=True)
    passport_number = models.CharField(max_length=50, blank=True)
    cnic_number = models.CharField(max_length=50, blank=True)
    phone_number = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return self.full_name or 'Passenger'


class BookingTicket(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='tickets')
    passenger_name = models.CharField(max_length=150, blank=True)
    passport_number = models.CharField(max_length=50, blank=True)
    ticket_seat = models.CharField(max_length=30, blank=True)


class BookingHotel(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='hotels')
    city = models.CharField(max_length=100, default='Makkah')
    hotel_name = models.CharField(max_length=150, blank=True)
    nights = models.PositiveIntegerField(default=1)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES, default='single')
    no_of_rooms = models.PositiveIntegerField(default=1)
    check_in = models.DateField(null=True, blank=True)
    check_out = models.DateField(null=True, blank=True)


class BookingRoute(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='routes')
    route = models.CharField(max_length=200, blank=True)
    transport_type = models.CharField(max_length=30, choices=TRANSPORT_TYPE_CHOICES, default='private_car')
    notes = models.CharField(max_length=200, blank=True)


class BookingVisa(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='visas')
    passport_number = models.CharField(max_length=50, blank=True)
    full_name = models.CharField(max_length=150, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    visa_company = models.CharField(max_length=150, blank=True)
    send_to = models.CharField(max_length=150, blank=True)
    status = models.CharField(max_length=20, choices=BOOKING_VISA_STATUS_CHOICES, default='pending')

# ============================================================
# PACKAGE MODULE (Hajj / Umrah Packages)
# ============================================================

MEDINA_ARRIVAL_CHOICES = [
    ('before_hajj', 'Before Hajj'),
    ('after_hajj', 'After Hajj'),
]

HAJJ_DURATION_CHOICES = [
    ('short', 'Short'),
    ('long', 'Long'),
]

HIJRI_MONTH_CHOICES = [
    ('muharram', 'Muharram'), ('safar', 'Safar'), ('rabi_ul_awwal', "Rabi' al-Awwal"),
    ('rabi_ul_thani', "Rabi' al-Thani"), ('jumada_ul_awwal', 'Jumada al-Awwal'),
    ('jumada_ul_thani', 'Jumada al-Thani'), ('rajab', 'Rajab'), ('shaban', "Sha'ban"),
    ('ramadan', 'Ramadan'), ('shawwal', 'Shawwal'), ('dhul_qadah', "Dhul-Qa'dah"),
    ('dhul_hijjah', 'Dhul-Hijjah'),
]

PACKAGE_ROOM_SHARING_CHOICES = [
    ('double', 'Double'), ('triple', 'Triple'), ('quad', 'Quad'), ('sharing', 'Sharing'),
]

PACKAGE_ACCOMMODATION_TYPE_CHOICES = [
    ('hotel', 'Hotel'), ('apartment', 'Apartment'), ('camp', 'Camp'),
]

SAUDI_STAR_RATING_CHOICES = [
    ('1', '1 Star'), ('2', '2 Star'), ('3', '3 Star'), ('4', '4 Star'), ('5', '5 Star'),
]

PACKAGE_FOOD_CHOICES = [
    ('full_board', 'Full Board'), ('half_board', 'Half Board'),
    ('breakfast_only', 'Breakfast Only'), ('no_meals', 'No Meals'),
]

YES_NO_CHOICES = [('yes', 'Yes'), ('no', 'No')]

PACKAGE_PLACE_CHOICES = [
    ('makkah', 'Makkah'), ('madinah', 'Madinah'), ('azizia', 'Azizia'), ('mina', 'Mina'),
]

FLIGHT_CLASS_CHOICES = [
    ('economy', 'Economy'), ('business', 'Business'), ('first', 'First'),
]


class Package(models.Model):
    # Package tab
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='packages')
    package_number = models.CharField('Package #', max_length=50, blank=True)
    category = models.CharField(max_length=100, blank=True)
    zone = models.CharField(max_length=100, blank=True)
    package_name = models.CharField(max_length=200, blank=True)
    package_code = models.CharField(max_length=50, blank=True)
    days = models.PositiveIntegerField(null=True, blank=True)
    year = models.PositiveIntegerField(default=2026)
    maktab = models.CharField(max_length=100, blank=True)
    maktab_number = models.CharField(max_length=50, blank=True)
    medina_arrival = models.CharField(max_length=20, choices=MEDINA_ARRIVAL_CHOICES, default='before_hajj')
    hajj_duration = models.CharField(max_length=10, choices=HAJJ_DURATION_CHOICES, default='short')
    hijri_start_day = models.PositiveSmallIntegerField(null=True, blank=True)
    hijri_start_month = models.CharField(max_length=20, choices=HIJRI_MONTH_CHOICES, blank=True)

    # Package Category
    room_type = models.CharField(max_length=100, blank=True)
    azizia_room_type = models.CharField(max_length=100, blank=True)
    makkah_type = models.CharField(max_length=20, choices=PACKAGE_ROOM_SHARING_CHOICES, blank=True)
    medinah_type = models.CharField(max_length=20, choices=PACKAGE_ROOM_SHARING_CHOICES, blank=True)
    azizia_type = models.CharField(max_length=20, choices=PACKAGE_ROOM_SHARING_CHOICES, blank=True)
    mina_type = models.CharField(max_length=100, blank=True)

    # Makkah / Madinah Sharing Breakdown
    makkah_a_double = models.PositiveIntegerField(default=0)
    makkah_a_triple = models.PositiveIntegerField(default=0)
    makkah_a_quad = models.PositiveIntegerField(default=0)
    makkah_a_sharing = models.PositiveIntegerField(default=0)

    makkah_b_double = models.PositiveIntegerField(default=0)
    makkah_b_triple = models.PositiveIntegerField(default=0)
    makkah_b_quad = models.PositiveIntegerField(default=0)
    makkah_b_sharing = models.PositiveIntegerField(default=0)

    madinah_a_double = models.PositiveIntegerField(default=0)
    madinah_a_triple = models.PositiveIntegerField(default=0)
    madinah_a_quad = models.PositiveIntegerField(default=0)
    madinah_a_sharing = models.PositiveIntegerField(default=0)

    madinah_b_double = models.PositiveIntegerField(default=0)
    madinah_b_triple = models.PositiveIntegerField(default=0)
    madinah_b_quad = models.PositiveIntegerField(default=0)
    madinah_b_sharing = models.PositiveIntegerField(default=0)

    # Training / Gifts tab
    giveaways = models.TextField(blank=True)

    # Terms & Condition tab
    terms_condition = models.TextField(blank=True)

    # Itinerary tab
    itinerary_description = models.TextField(blank=True)
    itinerary_image_mina = models.ImageField(upload_to='packages/itinerary/', null=True, blank=True)
    itinerary_image_arafat = models.ImageField(upload_to='packages/itinerary/', null=True, blank=True)
    itinerary_image_muzdalifah = models.ImageField(upload_to='packages/itinerary/', null=True, blank=True)
    itinerary_image_rami_day1 = models.ImageField(upload_to='packages/itinerary/', null=True, blank=True)
    itinerary_image_rami_day2 = models.ImageField(upload_to='packages/itinerary/', null=True, blank=True)
    itinerary_image_rami_day3 = models.ImageField(upload_to='packages/itinerary/', null=True, blank=True)

    # Maktab Address tab
    maktab_address = models.CharField(max_length=255, blank=True)
    office_address = models.CharField(max_length=255, blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='packages_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.package_name or self.package_code or f'Package #{self.pk}'


class PackageAccommodation(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='accommodations')
    place = models.CharField(max_length=20, choices=PACKAGE_PLACE_CHOICES, blank=True)
    check_in = models.DateField(null=True, blank=True)
    check_out = models.DateField(null=True, blank=True)
    same_hotel_for_both = models.BooleanField(default=False)

    accommodation_type_a = models.CharField(max_length=20, choices=PACKAGE_ACCOMMODATION_TYPE_CHOICES, blank=True)
    saudi_star_rating_a = models.CharField(max_length=5, choices=SAUDI_STAR_RATING_CHOICES, blank=True)
    hotel_a = models.CharField(max_length=150, blank=True)

    accommodation_type_b = models.CharField(max_length=20, choices=PACKAGE_ACCOMMODATION_TYPE_CHOICES, blank=True)
    saudi_star_rating_b = models.CharField(max_length=5, choices=SAUDI_STAR_RATING_CHOICES, blank=True)
    hotel_b = models.CharField(max_length=150, blank=True)

    distance_meter = models.PositiveIntegerField(null=True, blank=True)
    azizia_date = models.DateField(null=True, blank=True)
    food_package = models.CharField(max_length=20, choices=PACKAGE_FOOD_CHOICES, blank=True)
    accommodation_days = models.PositiveIntegerField(null=True, blank=True)

    actual_check_in_time = models.DateTimeField(null=True, blank=True)
    actual_check_out_time = models.DateTimeField(null=True, blank=True)
    nights = models.PositiveIntegerField(null=True, blank=True)

    makkah_ziarat = models.CharField(max_length=5, choices=YES_NO_CHOICES, blank=True)
    madinah_ziarat = models.CharField(max_length=5, choices=YES_NO_CHOICES, blank=True)
    distribution = models.CharField(max_length=150, blank=True)

    camp = models.CharField(max_length=150, blank=True)
    arafat = models.CharField(max_length=150, blank=True)
    azizia_shuttle = models.CharField(max_length=150, blank=True)

    bedding_sofa_mattress = models.CharField(max_length=150, blank=True)
    sharing_room_tent_camp = models.CharField(max_length=150, blank=True)
    sharing_type = models.CharField(max_length=150, blank=True)

    note = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f'{self.get_place_display() or "Accommodation"} - {self.hotel_a or self.hotel_b}'


class PackageTransport(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='transports')
    route = models.CharField(max_length=200, blank=True)
    arrival = models.CharField(max_length=100, blank=True)
    departure = models.CharField(max_length=100, blank=True)
    type = models.CharField(max_length=100, blank=True)
    vehicle = models.CharField(max_length=100, blank=True)


class PackageFlight(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='flights')
    airline = models.CharField(max_length=100, blank=True)
    flight_no = models.CharField(max_length=30, blank=True)
    flight_class = models.CharField(max_length=20, choices=FLIGHT_CLASS_CHOICES, blank=True)
    origin = models.CharField(max_length=100, blank=True)
    destination = models.CharField(max_length=100, blank=True)
    departure_date = models.DateField(null=True, blank=True)
    departure_time = models.TimeField(null=True, blank=True)
    arrival_date = models.DateField(null=True, blank=True)
    arrival_time = models.TimeField(null=True, blank=True)
    pnr_no = models.CharField(max_length=50, blank=True)
    ticket_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_preferred = models.CharField(max_length=5, choices=YES_NO_CHOICES, default='no')


class PackageTrain(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='trains')
    railway = models.CharField(max_length=100, blank=True)
    train_no = models.CharField(max_length=30, blank=True)
    train_class = models.CharField(max_length=50, blank=True)
    origin = models.CharField(max_length=100, blank=True)
    destination = models.CharField(max_length=100, blank=True)
    departure_date = models.DateField(null=True, blank=True)
    departure_time = models.TimeField(null=True, blank=True)
    arrival_date = models.DateField(null=True, blank=True)
    arrival_time = models.TimeField(null=True, blank=True)
    pnr_no = models.CharField(max_length=50, blank=True)
    ticket_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)


# ============================================================
# VISA MANAGEMENT MODULE (Section 10 of requirements)
# ============================================================

VISA_APPLICATION_STATUS_CHOICES = [
    ('documents_required', 'Documents Required'),
    ('documents_received', 'Documents Received'),
    ('submitted', 'Submitted'),
    ('processing', 'Processing'),
    ('appointment', 'Appointment Scheduled'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('passport_returned', 'Passport Returned'),
    ('completed', 'Completed'),
]

VISA_CATEGORY_CHOICES = [
    ('tourist', 'Tourist'),
    ('business', 'Business'),
    ('umrah', 'Umrah'),
    ('hajj', 'Hajj'),
    ('work', 'Work'),
    ('student', 'Student'),
    ('transit', 'Transit'),
    ('family_visit', 'Family Visit'),
    ('other', 'Other'),
]


class VisaApplication(models.Model):
    lead = models.ForeignKey(
        Lead, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='visa_applications'
    )
    applicant_name = models.CharField(max_length=150)
    passport_number = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=100)
    visa_category = models.CharField(max_length=20, choices=VISA_CATEGORY_CHOICES, default='tourist')
    application_type = models.CharField(max_length=100, blank=True, null=True)
    embassy_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    service_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    processing_time_days = models.PositiveIntegerField(blank=True, null=True)
    assigned_agent = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='visa_applications'
    )
    status = models.CharField(max_length=25, choices=VISA_APPLICATION_STATUS_CHOICES, default='documents_required')
    appointment_datetime = models.DateTimeField(blank=True, null=True)
    submission_date = models.DateField(blank=True, null=True)
    expected_decision_date = models.DateField(blank=True, null=True)
    decision_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.applicant_name} — {self.country} ({self.get_status_display()})"

    def is_deadline_near(self):
        if self.expected_decision_date:
            days = (self.expected_decision_date - timezone.localdate()).days
            return 0 <= days <= 3
        return False

    class Meta:
        ordering = ['-created_at']


VISA_DOC_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('received', 'Received'),
    ('not_applicable', 'Not Applicable'),
]


class VisaDocumentChecklistItem(models.Model):
    application = models.ForeignKey(
        VisaApplication, on_delete=models.CASCADE, related_name='checklist_items'
    )
    document_name = models.CharField(max_length=150)
    status = models.CharField(max_length=20, choices=VISA_DOC_STATUS_CHOICES, default='pending')
    file = models.FileField(upload_to='visa_documents/%Y/%m/', blank=True, null=True)
    notes = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.document_name} — {self.get_status_display()}"


# ═════════════════════════════════════════════════════════════
# TRAVEL AGENCY MODULES — Hotels, Suppliers, Transportation,
# Itineraries, Corporate Travel, Bulk Email, Reviews
# ═════════════════════════════════════════════════════════════

HOTEL_STAR_CHOICES = [
    ('1', '1 Star'), ('2', '2 Star'), ('3', '3 Star'),
    ('4', '4 Star'), ('5', '5 Star'), ('unrated', 'Unrated'),
]

MEAL_PLAN_CHOICES = [
    ('ro', 'Room Only'), ('bb', 'Bed & Breakfast'),
    ('hb', 'Half Board'), ('fb', 'Full Board'), ('ai', 'All Inclusive'),
]


class Hotel(models.Model):
    """Master hotel catalog — city hotels used across bookings/packages."""
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, blank=True)
    star_rating = models.CharField(max_length=10, choices=HOTEL_STAR_CHOICES, default='3')
    address = models.CharField(max_length=255, blank=True)
    contact_person = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.city})"


class HotelReservation(models.Model):
    RESERVATION_STATUS_CHOICES = [
        ('draft', 'Draft'), ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'), ('completed', 'Completed'),
    ]
    hotel = models.ForeignKey(Hotel, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations')
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='hotel_reservations')
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='hotel_reservations')
    room_type = models.CharField(max_length=100, blank=True)
    meal_plan = models.CharField(max_length=10, choices=MEAL_PLAN_CHOICES, default='bb')
    check_in = models.DateField(null=True, blank=True)
    check_out = models.DateField(null=True, blank=True)
    nights = models.PositiveIntegerField(default=1)
    rooms = models.PositiveIntegerField(default=1)
    rate_per_night = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    confirmation_number = models.CharField(max_length=100, blank=True)
    cancellation_policy = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=RESERVATION_STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-check_in']

    def __str__(self):
        return f"{self.hotel} — {self.check_in} to {self.check_out}"

    def total_cost(self):
        return (self.rate_per_night or 0) * (self.nights or 0) * (self.rooms or 1)


SUPPLIER_TYPE_CHOICES = [
    ('airline', 'Airline'), ('hotel', 'Hotel'), ('transport', 'Transport Provider'),
    ('visa_partner', 'Visa Partner'), ('other', 'Other Vendor'),
]


class Supplier(models.Model):
    """Airlines, hotels, transport providers, visa partners and other vendors."""
    name = models.CharField(max_length=200)
    supplier_type = models.CharField(max_length=20, choices=SUPPLIER_TYPE_CHOICES, default='other')
    contact_person = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    rates_notes = models.TextField(blank=True, help_text='Rate sheet notes / negotiated rates')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_supplier_type_display()})"


VEHICLE_TYPE_CHOICES = [
    ('sedan', 'Sedan'), ('suv', 'SUV'), ('van', 'Van'),
    ('coaster', 'Coaster (22-seat)'), ('bus', 'Bus'), ('luxury', 'Luxury Car'),
]

TRANSFER_TYPE_CHOICES = [
    ('airport_pickup', 'Airport Pickup'), ('airport_dropoff', 'Airport Drop-off'),
    ('full_day', 'Full-Day Car'), ('intercity', 'Intercity Transfer'), ('sightseeing', 'Sightseeing'),
]

TRANSPORT_STATUS_CHOICES = [
    ('scheduled', 'Scheduled'), ('assigned', 'Driver Assigned'),
    ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled'),
]


class Vehicle(models.Model):
    """Fleet / contracted vehicle used for transportation module."""
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPE_CHOICES, default='sedan')
    make_model = models.CharField(max_length=150, blank=True)
    plate_number = models.CharField(max_length=50, blank=True)
    capacity = models.PositiveIntegerField(default=4)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehicles')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_vehicle_type_display()} — {self.plate_number or self.make_model}"


class TransportSchedule(models.Model):
    """Airport transfers, full-day cars, drivers, pickup/drop-off schedule."""
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='transport_schedules')
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='transport_schedules')
    group = models.ForeignKey('PilgrimGroup', on_delete=models.SET_NULL, null=True, blank=True, related_name='transport_schedules')
    pilgrims = models.ManyToManyField('Pilgrim', blank=True, related_name='transport_assignments')
    transfer_type = models.CharField(max_length=20, choices=TRANSFER_TYPE_CHOICES, default='airport_pickup')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='schedules')
    driver_name = models.CharField(max_length=150, blank=True)
    driver_phone = models.CharField(max_length=50, blank=True)
    pickup_location = models.CharField(max_length=255, blank=True)
    dropoff_location = models.CharField(max_length=255, blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=TRANSPORT_STATUS_CHOICES, default='scheduled')
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-scheduled_at']

    def __str__(self):
        return f"{self.get_transfer_type_display()} — {self.pickup_location or ''} → {self.dropoff_location or ''}"


TOUR_TYPE_CHOICES = [
    ('group', 'Group Tour'), ('private', 'Private Tour'), ('customized', 'Customized Tour'),
    ('honeymoon', 'Honeymoon Tour'), ('corporate', 'Corporate Tour'), ('sightseeing', 'Sightseeing / Excursion'),
]


class Itinerary(models.Model):
    """Day-by-day itinerary builder, shared across tour types."""
    title = models.CharField(max_length=200)
    tour_type = models.CharField(max_length=15, choices=TOUR_TYPE_CHOICES, default='group')
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='itineraries')
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='itineraries')
    package = models.ForeignKey(Package, on_delete=models.SET_NULL, null=True, blank=True, related_name='itineraries')
    destination = models.CharField(max_length=150, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='itineraries_created')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Itineraries'

    def __str__(self):
        return self.title


class ItineraryDay(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='days')
    day_number = models.PositiveIntegerField(default=1)
    date = models.DateField(null=True, blank=True)
    title = models.CharField(max_length=200, blank=True)
    activities = models.TextField(blank=True, help_text='Activities, sightseeing, transfers')
    meals = models.CharField(max_length=150, blank=True)
    hotel_detail = models.CharField(max_length=200, blank=True)
    flight_detail = models.CharField(max_length=200, blank=True)
    instructions = models.TextField(blank=True)

    class Meta:
        ordering = ['day_number']

    def __str__(self):
        return f"Day {self.day_number} — {self.title or self.itinerary.title}"


TRAVEL_REQUEST_STATUS_CHOICES = [
    ('pending', 'Pending Approval'), ('approved', 'Approved'),
    ('rejected', 'Rejected'), ('booked', 'Booked'),
]


class CorporateTravelRequest(models.Model):
    """Employee travel request under a corporate account — approvals, rates, billing."""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='travel_requests')
    employee = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='travel_requests')
    purpose = models.CharField(max_length=255, blank=True)
    destination = models.CharField(max_length=150, blank=True)
    travel_date = models.DateField(null=True, blank=True)
    return_date = models.DateField(null=True, blank=True)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    corporate_rate_applied = models.BooleanField(default=True)
    status = models.CharField(max_length=15, choices=TRAVEL_REQUEST_STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_travel_requests')
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='corporate_requests')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.company.name} — {self.destination} ({self.get_status_display()})"


BULK_EMAIL_STATUS_CHOICES = [
    ('draft', 'Draft'), ('sending', 'Sending'), ('sent', 'Sent'), ('failed', 'Failed'),
]


class BulkEmailCampaign(models.Model):
    """Bulk/segment email campaigns — separate from normal one-to-one email."""
    name = models.CharField(max_length=200)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    filter_destination = models.CharField(max_length=150, blank=True)
    filter_trip_type = models.CharField(max_length=30, blank=True)
    filter_lead_status = models.CharField(max_length=30, blank=True)
    filter_country = models.CharField(max_length=100, blank=True)
    recipient_count = models.PositiveIntegerField(default=0)
    sent_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=BULK_EMAIL_STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='bulk_campaigns')
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class BulkEmailRecipient(models.Model):
    campaign = models.ForeignKey(BulkEmailCampaign, on_delete=models.CASCADE, related_name='recipients')
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True)
    email = models.EmailField()
    status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('sent', 'Sent'), ('failed', 'Failed')], default='pending')
    sent_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.email} — {self.get_status_display()}"


class Review(models.Model):
    """Customer feedback / reviews after travel completion."""
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    rating = models.PositiveSmallIntegerField(default=5, help_text='1-5 stars')
    comment = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.lead} — {self.rating}★"


# ==========================================================================
#  PILGRIM / GROUP / DOCUMENT / PROFIT  —  Hajj & Umrah specific modules
#  (requirements doc sections 3, 4, 5, 13)
# ==========================================================================

GENDER_CHOICES = [
    ('male', 'Male'),
    ('female', 'Female'),
]

BLOOD_GROUP_CHOICES = [
    ('a+', 'A+'), ('a-', 'A-'), ('b+', 'B+'), ('b-', 'B-'),
    ('ab+', 'AB+'), ('ab-', 'AB-'), ('o+', 'O+'), ('o-', 'O-'),
]

RELATIONSHIP_CHOICES = [
    ('leader', 'Group Leader'),
    ('husband', 'Husband'),
    ('wife', 'Wife'),
    ('son', 'Son'),
    ('daughter', 'Daughter'),
    ('father', 'Father'),
    ('mother', 'Mother'),
    ('brother', 'Brother'),
    ('sister', 'Sister'),
    ('relative', 'Other Relative'),
    ('friend', 'Friend'),
    ('other', 'Other'),
]

PILGRIM_STATUS_CHOICES = [
    ('registered', 'Registered'),
    ('documents_pending', 'Documents Pending'),
    ('visa_processing', 'Visa Processing'),
    ('ready', 'Ready to Travel'),
    ('travelling', 'Travelling'),
    ('returned', 'Returned'),
    ('cancelled', 'Cancelled'),
]

PILGRIM_TRIP_CHOICES = [
    ('hajj', 'Hajj'),
    ('umrah', 'Umrah'),
    ('ziyarat', 'Ziyarat'),
    ('tour', 'Tour'),
]


class PilgrimGroup(models.Model):
    """Family / group ka container — Hajj & Umrah mein sabse zaroori entity."""
    group_id = models.CharField(max_length=30, unique=True, blank=True)
    name = models.CharField(max_length=150, help_text='e.g. KHAN FAMILY')
    trip_type = models.CharField(max_length=20, choices=PILGRIM_TRIP_CHOICES, default='umrah')
    season_year = models.PositiveIntegerField(default=2026)
    package = models.ForeignKey('Package', on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='pilgrim_groups')
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='pilgrim_groups')
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='pilgrim_groups')
    departure_date = models.DateField(null=True, blank=True)
    return_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.group_id:
            prefix = 'HJ' if self.trip_type == 'hajj' else 'UMR'
            last = PilgrimGroup.objects.filter(group_id__startswith=prefix).count() + 1
            self.group_id = f"{prefix}-{self.season_year}-{last:04d}"
        super().save(*args, **kwargs)

    @property
    def leader(self):
        return self.pilgrims.filter(relationship='leader').first() or self.pilgrims.first()

    @property
    def total_pilgrims(self):
        return self.pilgrims.count()

    @property
    def visa_approved_count(self):
        return self.pilgrims.filter(visa_status='approved').count()

    @property
    def documents_complete_count(self):
        return sum(1 for p in self.pilgrims.all() if p.documents_complete)

    def __str__(self):
        return f"{self.name} ({self.group_id})"


class Pilgrim(models.Model):
    """Lead convert hone ke baad ka complete pilgrim profile."""
    pilgrim_id = models.CharField(max_length=30, unique=True, blank=True)
    group = models.ForeignKey(PilgrimGroup, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='pilgrims')
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='pilgrims')
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='pilgrims')

    # Personal
    full_name = models.CharField(max_length=150)
    father_husband_name = models.CharField(max_length=150, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='male')
    nationality = models.CharField(max_length=80, default='Pakistani')
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True)
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES, default='leader')

    # Identity
    cnic = models.CharField(max_length=30, blank=True)
    passport_number = models.CharField(max_length=40, blank=True)
    passport_expiry = models.DateField(null=True, blank=True)

    # Contact
    phone = models.CharField(max_length=30, blank=True)
    whatsapp = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_phone = models.CharField(max_length=30, blank=True)

    # Travel
    trip_type = models.CharField(max_length=20, choices=PILGRIM_TRIP_CHOICES, default='umrah')
    status = models.CharField(max_length=25, choices=PILGRIM_STATUS_CHOICES, default='registered')
    visa_status = models.CharField(max_length=25, choices=VISA_APPLICATION_STATUS_CHOICES,
                                   default='documents_required')
    room_number = models.CharField(max_length=30, blank=True)
    flight_number = models.CharField(max_length=30, blank=True)
    seat_number = models.CharField(max_length=20, blank=True)
    travel_history = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['group', 'relationship', 'full_name']

    def save(self, *args, **kwargs):
        if not self.pilgrim_id:
            year = timezone.localdate().year
            seq = Pilgrim.objects.filter(pilgrim_id__startswith=f'P-{year}').count() + 1
            self.pilgrim_id = f"P-{year}-{seq:04d}"
        super().save(*args, **kwargs)

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = timezone.localdate()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def passport_days_left(self):
        if not self.passport_expiry:
            return None
        return (self.passport_expiry - timezone.localdate()).days

    @property
    def passport_alert(self):
        """None / 'expired' / 'expiring' — 6 mahine se kam rehne par warning."""
        days = self.passport_days_left
        if days is None:
            return None
        if days < 0:
            return 'expired'
        if days <= 180:
            return 'expiring'
        return None

    @property
    def documents_complete(self):
        required = {'passport', 'cnic', 'photo'}
        have = set(
            self.pilgrim_documents.filter(status__in=['uploaded', 'approved'])
            .values_list('document_type', flat=True)
        )
        return required.issubset(have)

    def __str__(self):
        return f"{self.full_name} ({self.pilgrim_id})"


PILGRIM_DOC_TYPE_CHOICES = [
    ('passport', 'Passport'),
    ('cnic', 'CNIC'),
    ('photo', 'Passport Photo'),
    ('visa', 'Visa'),
    ('vaccination', 'Vaccination Certificate'),
    ('medical', 'Medical Certificate'),
    ('insurance', 'Travel Insurance'),
    ('ticket', 'Flight Ticket'),
    ('hotel_voucher', 'Hotel Voucher'),
    ('transport_voucher', 'Transport Voucher'),
    ('other', 'Other Document'),
]

PILGRIM_DOC_STATUS_CHOICES = [
    ('not_uploaded', 'Not Uploaded'),
    ('uploaded', 'Uploaded'),
    ('under_review', 'Under Review'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('expired', 'Expired'),
]


class PilgrimDocument(models.Model):
    """Per-pilgrim document tracking with expiry alerts."""
    pilgrim = models.ForeignKey(Pilgrim, on_delete=models.CASCADE, related_name='pilgrim_documents')
    document_type = models.CharField(max_length=25, choices=PILGRIM_DOC_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=PILGRIM_DOC_STATUS_CHOICES, default='not_uploaded')
    file = models.FileField(upload_to='pilgrim_documents/%Y/%m/', blank=True, null=True)
    document_number = models.CharField(max_length=60, blank=True)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['pilgrim', 'document_type']
        unique_together = [('pilgrim', 'document_type')]

    @property
    def days_to_expiry(self):
        if not self.expiry_date:
            return None
        return (self.expiry_date - timezone.localdate()).days

    @property
    def is_expiring(self):
        d = self.days_to_expiry
        return d is not None and 0 <= d <= 180

    @property
    def is_expired(self):
        d = self.days_to_expiry
        return d is not None and d < 0

    def __str__(self):
        return f"{self.pilgrim.full_name} — {self.get_document_type_display()}"


class BookingCost(models.Model):
    """
    Supplier-side cost breakdown per booking, taake CEO ko actual
    gross profit aur margin dikhe (requirements doc section 13).
    """
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='cost')
    hotel_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    flight_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    visa_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transport_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    food_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ziyarat_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    guide_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    insurance_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_cost(self):
        return (self.hotel_cost + self.flight_cost + self.visa_cost +
                self.transport_cost + self.food_cost + self.ziyarat_cost +
                self.guide_cost + self.insurance_cost + self.other_cost)

    @property
    def selling_price(self):
        return self.booking.total_amount

    @property
    def gross_profit(self):
        return self.selling_price - self.total_cost

    @property
    def margin_percent(self):
        sp = self.selling_price
        if not sp:
            return 0
        return round(float(self.gross_profit) / float(sp) * 100, 1)

    def __str__(self):
        return f"Cost for {self.booking}"


# ==========================================================================
#  FLIGHT PASSENGER ASSIGNMENT  (requirements doc section 9.3)
#  Booking-level flight legs with per-pilgrim passenger assignment.
# ==========================================================================

FLIGHT_LEG_CHOICES = [
    ('outbound', 'Outbound'),
    ('return', 'Return'),
    ('internal', 'Internal / Connecting'),
]

BOOKING_FLIGHT_STATUS_CHOICES = [
    ('scheduled', 'Scheduled'),
    ('ticketed', 'Ticketed'),
    ('changed', 'Changed'),
    ('cancelled', 'Cancelled'),
    ('completed', 'Completed'),
]


class BookingFlight(models.Model):
    """An actual booked flight leg — outbound/return — with passenger assignment."""
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='booking_flights')
    group = models.ForeignKey('PilgrimGroup', on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='booking_flights')
    leg = models.CharField(max_length=10, choices=FLIGHT_LEG_CHOICES, default='outbound')
    airline = models.CharField(max_length=100, blank=True)
    flight_no = models.CharField(max_length=30, blank=True)
    pnr = models.CharField(max_length=50, blank=True)
    origin = models.CharField(max_length=100, blank=True)
    destination = models.CharField(max_length=100, blank=True)
    departure_date = models.DateField(null=True, blank=True)
    departure_time = models.TimeField(null=True, blank=True)
    arrival_date = models.DateField(null=True, blank=True)
    arrival_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=BOOKING_FLIGHT_STATUS_CHOICES, default='scheduled')
    ticket_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['departure_date', 'departure_time']

    @property
    def passenger_count(self):
        return self.passengers.count()

    def __str__(self):
        return f"{self.get_leg_display()} {self.flight_no or ''} — {self.origin} → {self.destination}"


class BookingFlightPassenger(models.Model):
    """Passenger assignment — links a specific pilgrim to a specific flight leg."""
    flight = models.ForeignKey(BookingFlight, on_delete=models.CASCADE, related_name='passengers')
    pilgrim = models.ForeignKey('Pilgrim', on_delete=models.CASCADE, related_name='flight_assignments')
    seat_number = models.CharField(max_length=20, blank=True)
    baggage = models.CharField(max_length=50, blank=True)
    ticket_number = models.CharField(max_length=50, blank=True)

    class Meta:
        unique_together = [('flight', 'pilgrim')]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # keep the pilgrim's own flight/seat fields in sync for quick reference,
        # regardless of whether this was created from the view, admin, or a script
        Pilgrim.objects.filter(pk=self.pilgrim_id).update(
            flight_number=self.flight.flight_no, seat_number=self.seat_number)

    def __str__(self):
        return f"{self.pilgrim.full_name} on {self.flight}"


# ==========================================================================
#  ZIYARAT / ACTIVITIES  (requirements doc section 9.6)
# ==========================================================================

ZIYARAT_CITY_CHOICES = [
    ('makkah', 'Makkah'),
    ('madinah', 'Madinah'),
    ('jeddah', 'Jeddah'),
    ('taif', 'Taif'),
    ('other', 'Other'),
]


class ZiyaratActivity(models.Model):
    """A ziyarat / sightseeing activity — linked to a booking or group, with participants."""
    name = models.CharField(max_length=150, help_text='e.g. Jabal-e-Noor, Masjid-e-Quba')
    city = models.CharField(max_length=15, choices=ZIYARAT_CITY_CHOICES, default='makkah')
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='ziyarat_activities')
    group = models.ForeignKey('PilgrimGroup', on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='ziyarat_activities')
    transport = models.ForeignKey('TransportSchedule', on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='ziyarat_activities')
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(default=60)
    guide_name = models.CharField(max_length=150, blank=True)
    guide_phone = models.CharField(max_length=30, blank=True)
    is_included = models.BooleanField(default=True, help_text='Included in package vs paid add-on')
    price_per_person = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['date', 'time']
        verbose_name_plural = 'Ziyarat Activities'

    @property
    def participant_count(self):
        return self.participants.count()

    @property
    def total_addon_revenue(self):
        if self.is_included:
            return 0
        return self.price_per_person * self.participant_count

    def __str__(self):
        return f"{self.name} ({self.get_city_display()})"


class ZiyaratParticipant(models.Model):
    activity = models.ForeignKey(ZiyaratActivity, on_delete=models.CASCADE, related_name='participants')
    pilgrim = models.ForeignKey('Pilgrim', on_delete=models.CASCADE, related_name='ziyarat_participations')
    attended = models.BooleanField(default=False)

    class Meta:
        unique_together = [('activity', 'pilgrim')]

    def __str__(self):
        return f"{self.pilgrim.full_name} — {self.activity.name}"


# ==========================================================================
#  FINANCE & COMMERCIAL MANAGEMENT  (requirements doc section 11)
#  Booking total -> installment schedule -> transaction/receipt ->
#  outstanding balance -> aging -> refunds with approval.
# ==========================================================================

PAYMENT_METHOD_CHOICES = [
    ('cash', 'Cash'),
    ('bank_transfer', 'Bank Transfer'),
    ('card', 'Credit / Debit Card'),
    ('easypaisa', 'Easypaisa'),
    ('jazzcash', 'JazzCash'),
    ('cheque', 'Cheque'),
    ('other', 'Other'),
]

INSTALLMENT_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('partial', 'Partially Paid'),
    ('paid', 'Paid'),
    ('overdue', 'Overdue'),
]

FIN_TRANSACTION_TYPE_CHOICES = [
    ('payment', 'Payment Received'),
    ('refund', 'Refund Issued'),
]

REFUND_STATUS_CHOICES = [
    ('pending', 'Pending Approval'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('completed', 'Completed'),
]


class BookingInstallment(models.Model):
    """One line of a booking's payment schedule (11.1)."""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='installments')
    label = models.CharField(max_length=80, default='Installment')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=10, choices=INSTALLMENT_STATUS_CHOICES, default='pending')
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['due_date']

    @property
    def amount_paid(self):
        paid = self.transactions.filter(transaction_type='payment').aggregate(
            s=models.Sum('amount'))['s'] or 0
        refunded = self.transactions.filter(transaction_type='refund').aggregate(
            s=models.Sum('amount'))['s'] or 0
        return paid - refunded

    @property
    def balance(self):
        return self.amount - self.amount_paid

    @property
    def days_overdue(self):
        if self.status == 'paid':
            return 0
        today = timezone.localdate()
        return max((today - self.due_date).days, 0)

    def refresh_status(self):
        paid = self.amount_paid
        if paid <= 0:
            self.status = 'overdue' if self.days_overdue > 0 else 'pending'
        elif paid < self.amount:
            self.status = 'partial'
        else:
            self.status = 'paid'
        self.save(update_fields=['status'])

    def __str__(self):
        return f"{self.label} — {self.booking} — Rs {self.amount}"


class BookingTransaction(models.Model):
    """Actual money movement — a receipt or a refund (11.1)."""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='transactions')
    installment = models.ForeignKey(BookingInstallment, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=FIN_TRANSACTION_TYPE_CHOICES, default='payment')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='bank_transfer')
    reference_number = models.CharField(max_length=80, blank=True, help_text='Transaction / cheque / slip number')
    receipt_number = models.CharField(max_length=30, unique=True, blank=True)
    transaction_date = models.DateTimeField(default=timezone.now)
    notes = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='booking_transactions')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-transaction_date']

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            year = timezone.localdate().year
            prefix = 'RFD' if self.transaction_type == 'refund' else 'RCPT'
            seq = BookingTransaction.objects.filter(
                receipt_number__startswith=f'{prefix}-{year}').count() + 1
            self.receipt_number = f"{prefix}-{year}-{seq:05d}"
        super().save(*args, **kwargs)
        if self.installment_id:
            self.installment.refresh_status()

    def __str__(self):
        return f"{self.receipt_number} — Rs {self.amount} ({self.get_transaction_type_display()})"


class RefundRequest(models.Model):
    """Refund / cancellation request requiring approval before money moves (11.1, 11.3)."""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='refund_requests')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=REFUND_STATUS_CHOICES, default='pending')
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='refund_requests_made')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='refund_requests_approved')
    requested_at = models.DateTimeField(default=timezone.now)
    decided_at = models.DateTimeField(null=True, blank=True)
    decision_notes = models.CharField(max_length=255, blank=True)
    transaction = models.OneToOneField(BookingTransaction, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='refund_request')

    class Meta:
        ordering = ['-requested_at']

    def approve_and_process(self, user, payment_method='bank_transfer', reference_number=''):
        """CEO/Finance approves — this creates the actual refund transaction (11.3: audit trail, no hard delete)."""
        txn = BookingTransaction.objects.create(
            booking=self.booking, transaction_type='refund', amount=self.amount,
            payment_method=payment_method, reference_number=reference_number,
            notes=f'Refund approved: {self.reason[:120]}', created_by=user,
        )
        self.status = 'completed'
        self.approved_by = user
        self.decided_at = timezone.localtime()
        self.transaction = txn
        self.save(update_fields=['status', 'approved_by', 'decided_at', 'transaction'])
        return txn

    def reject(self, user, notes=''):
        self.status = 'rejected'
        self.approved_by = user
        self.decided_at = timezone.localtime()
        self.decision_notes = notes
        self.save(update_fields=['status', 'approved_by', 'decided_at', 'decision_notes'])

    def __str__(self):
        return f"Refund Rs {self.amount} — {self.booking} ({self.get_status_display()})"

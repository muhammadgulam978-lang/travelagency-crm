from django.urls import path
from . import views
from . import views_travel as vt
from . import views_dashboard as vd
from . import views_pilgrims as vp
from . import views_finance as vf
from . import views_ziyarat as vz

urlpatterns = [
    path('', vd.dashboard, name='dashboard'),
    path('analytics/', vd.analytics_dashboard, name='analytics_dashboard'),
    path('calendar/', views.calendar_view, name='calendar_view'),

    # ---- Pilgrims / Groups / Profit / Kanban (Hajj & Umrah modules) ----
    path('pilgrims/', vp.pilgrim_list, name='pilgrim_list'),
    path('pilgrims/create/', vp.pilgrim_create, name='pilgrim_create'),
    path('pilgrims/<int:pk>/', vp.pilgrim_detail, name='pilgrim_detail'),
    path('pilgrims/<int:pk>/edit/', vp.pilgrim_edit, name='pilgrim_edit'),
    path('pilgrims/<int:pk>/documents/save/', vp.pilgrim_document_save, name='pilgrim_document_save'),
    path('leads/<int:pk>/convert-to-pilgrim/', vp.convert_lead_to_pilgrim, name='convert_lead_to_pilgrim'),

    path('groups/', vp.group_list, name='group_list'),
    path('groups/create/', vp.group_create, name='group_create'),
    path('groups/<int:pk>/', vp.group_detail, name='group_detail'),
    path('groups/<int:pk>/edit/', vp.group_edit, name='group_edit'),

    path('profit/', vp.profit_report, name='profit_report'),
    path('bookings/<int:pk>/cost/', vp.booking_cost_edit, name='booking_cost_edit'),

    path('pipeline/kanban/', vp.pipeline_kanban, name='pipeline_kanban'),

    # ---- Flights (per-pilgrim passenger assignment) ----
    path('flights/', vp.flight_list, name='flight_list'),
    path('flights/create/', vp.flight_create, name='flight_create'),
    path('flights/<int:pk>/', vp.flight_detail, name='flight_detail'),
    path('flights/<int:pk>/edit/', vp.flight_edit, name='flight_edit'),
    path('flights/<int:pk>/assign/', vp.flight_assign_passenger, name='flight_assign_passenger'),
    path('flights/<int:pk>/remove/<int:pilgrim_id>/', vp.flight_remove_passenger, name='flight_remove_passenger'),

    # ---- Transport (per-pilgrim/group assignment) ----
    path('transport/', vp.transport_list, name='transport_list'),
    path('transport/create/', vp.transport_create, name='transport_create'),
    path('transport/<int:pk>/', vp.transport_detail, name='transport_detail'),
    path('transport/<int:pk>/edit/', vp.transport_edit, name='transport_edit'),
    path('transport/<int:pk>/toggle/<int:pilgrim_id>/', vp.transport_toggle_pilgrim, name='transport_toggle_pilgrim'),

    # ---- Ziyarat / Activities ----
    path('ziyarat/', vz.ziyarat_list, name='ziyarat_list'),
    path('ziyarat/create/', vz.ziyarat_create, name='ziyarat_create'),
    path('ziyarat/<int:pk>/', vz.ziyarat_detail, name='ziyarat_detail'),
    path('ziyarat/<int:pk>/edit/', vz.ziyarat_edit, name='ziyarat_edit'),
    path('ziyarat/<int:pk>/toggle/<int:pilgrim_id>/', vz.ziyarat_toggle_participant, name='ziyarat_toggle_participant'),
    path('ziyarat/<int:pk>/attended/<int:pilgrim_id>/', vz.ziyarat_mark_attended, name='ziyarat_mark_attended'),

    # ---- Finance & Commercial Management ----
    path('receivables/', vf.receivables_list, name='receivables_list'),
    path('bookings/<int:pk>/finance/', vf.booking_finance_detail, name='booking_finance_detail'),
    path('bookings/<int:pk>/finance/installment/add/', vf.booking_installment_add, name='booking_installment_add'),
    path('bookings/<int:pk>/finance/payment/add/', vf.booking_transaction_add, name='booking_transaction_add'),
    path('bookings/<int:pk>/finance/refund/request/', vf.refund_request_create, name='refund_request_create'),
    path('receipts/<int:pk>/', vf.receipt_view, name='receipt_view'),
    path('refunds/', vf.refund_list, name='refund_list'),
    path('refunds/<int:pk>/approve/', vf.refund_approve, name='refund_approve'),
    path('refunds/<int:pk>/reject/', vf.refund_reject, name='refund_reject'),

    path('bookings/', views.booking_list, name='booking_list'),
    path('bookings/create/', views.booking_create, name='booking_create'),
    path('bookings/trash/', views.booking_trash, name='booking_trash'),
    path('bookings/<int:pk>/delete/', views.booking_delete, name='booking_delete'),
    path('bookings/<int:pk>/restore/', views.booking_restore, name='booking_restore'),
    path('bookings/<int:pk>/delete-permanent/', views.booking_delete_permanent, name='booking_delete_permanent'),

    # ---- Packages ----
    path('packages/', views.package_list, name='package_list'),
    path('packages/create/', views.package_create, name='package_create'),
    path('packages/trash/', views.package_trash, name='package_trash'),
    path('packages/<int:pk>/edit/', views.package_edit, name='package_edit'),
    path('packages/<int:pk>/view/', views.package_view, name='package_view'),
    path('packages/<int:pk>/delete/', views.package_delete, name='package_delete'),
    path('packages/<int:pk>/restore/', views.package_restore, name='package_restore'),
    path('packages/<int:pk>/delete-permanent/', views.package_delete_permanent, name='package_delete_permanent'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Users
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),

    # Companies
    path('companies/', views.company_list, name='company_list'),
    path('companies/create/', views.company_create, name='company_create'),
    path('companies/<int:pk>/', views.company_detail, name='company_detail'),
    path('companies/<int:pk>/edit/', views.company_edit, name='company_edit'),
    path('companies/<int:pk>/delete/', views.company_delete, name='company_delete'),

    # Contacts
    path('contacts/', views.contact_list, name='contact_list'),
    path('contacts/create/', views.contact_create, name='contact_create'),
    path('contacts/<int:pk>/edit/', views.contact_edit, name='contact_edit'),
    path('contacts/<int:pk>/delete/', views.contact_delete, name='contact_delete'),

    # Leads
    path('leads/create/', views.create_lead, name='create_lead'),
    path('leads/', views.lead_list, name='all_leads'),
    path('leads/status/<str:status>/', views.lead_list, name='lead_status_list'),
    path('leads/<int:pk>/', views.lead_detail, name='lead_detail'),
    path('leads/<int:pk>/edit/', views.lead_edit, name='lead_edit'),
    path('leads/<int:pk>/status/<str:status>/', views.update_lead_status, name='update_lead_status'),
    path('leads/<int:pk>/payment/add/', views.add_payment, name='add_payment'),
    path('leads/<int:pk>/delete/', views.lead_delete, name='lead_delete'),

    # Followups
    path('followups/<str:scope>/', views.followup_list, name='followup_list'),
    path('followups/<int:pk>/done/', views.followup_done, name='followup_done'),

    # Payments
    path('payments/advance/', views.payment_list, {'ptype': 'advance'}, name='payment_advance'),
    path('payments/full/', views.payment_list, {'ptype': 'full'}, name='payment_full'),
    path('payments/scheduled/', views.scheduled_payment_list, name='scheduled_payment_list'),
    path('payments/scheduled/create/', views.scheduled_payment_create, name='scheduled_payment_create'),
    path('payments/scheduled/<int:pk>/', views.scheduled_payment_detail, name='scheduled_payment_detail'),

    # Pipeline / Opportunities
    path('pipeline/', views.opportunity_pipeline, name='opportunity_pipeline'),
    path('opportunities/', views.opportunity_list, name='opportunity_list'),
    path('opportunities/create/', views.opportunity_create, name='opportunity_create'),
    path('opportunities/<int:pk>/', views.opportunity_detail, name='opportunity_detail'),
    path('opportunities/<int:pk>/edit/', views.opportunity_edit, name='opportunity_edit'),
    path('opportunities/<int:pk>/delete/', views.opportunity_delete, name='opportunity_delete'),
    path('opportunities/<int:pk>/move/<str:stage>/', views.opportunity_move, name='opportunity_move'),

    # Quotations
    path('quotations/', views.quotation_list, name='quotation_list'),
    path('quotations/create/', views.quotation_create, name='quotation_create'),
    path('quotations/<int:pk>/', views.quotation_detail, name='quotation_detail'),
    path('quotations/<int:pk>/pdf/', views.quotation_pdf, name='quotation_pdf'),

    # ---- Visa Applications ----
    path('visa/', views.visa_list, name='visa_list'),
    path('visa/create/', views.visa_create, name='visa_create'),
    path('visa/<int:pk>/', views.visa_detail, name='visa_detail'),
    path('visa/<int:pk>/edit/', views.visa_edit, name='visa_edit'),
    path('visa/<int:pk>/delete/', views.visa_delete, name='visa_delete'),
    path('visa/<int:pk>/checklist/<int:item_id>/update/', views.visa_checklist_update, name='visa_checklist_update'),
    path('quotations/<int:pk>/edit/', views.quotation_edit, name='quotation_edit'),
    path('quotations/<int:pk>/delete/', views.quotation_delete, name='quotation_delete'),
    path('quotations/<int:pk>/status/<str:status>/', views.quotation_status, name='quotation_status'),

    # Meetings
    path('meetings/', views.meeting_list, name='meeting_list'),
    path('meetings/create/', views.meeting_create, name='meeting_create'),
    path('meetings/<int:pk>/', views.meeting_detail, name='meeting_detail'),
    path('meetings/<int:pk>/edit/', views.meeting_edit, name='meeting_edit'),
    path('meetings/<int:pk>/delete/', views.meeting_delete, name='meeting_delete'),
    path('meetings/<int:pk>/status/<str:status>/', views.meeting_status, name='meeting_status'),

    # General Tasks
    path('general-tasks/', views.general_task_list, name='general_task_list'),
    path('general-tasks/create/', views.general_task_create, name='general_task_create'),
    path('general-tasks/<int:pk>/edit/', views.general_task_edit, name='general_task_edit'),
    path('general-tasks/<int:pk>/delete/', views.general_task_delete, name='general_task_delete'),
    path('general-tasks/<int:pk>/status/<str:status>/', views.general_task_status, name='general_task_status'),

    # Communication Log
    path('communications/', views.communication_list, name='communication_list'),
    path('communications/create/', views.communication_create, name='communication_create'),
    path('communications/<int:pk>/delete/', views.communication_delete, name='communication_delete'),
    path('communications/timeline/', views.communication_timeline, name='communication_timeline'),

    # Reports
    path('reports/', views.reports, name='reports'),

    # Activity Log
    path('activity/', views.activity_log, name='activity_log'),

    # Documents
    path('documents/', views.document_list, name='document_list'),
    path('documents/upload/', views.document_upload, name='document_upload'),
    path('documents/<int:pk>/delete/', views.document_delete, name='document_delete'),

    # Contracts
    path('contracts/', views.contract_list, name='contract_list'),
    path('contracts/create/', views.contract_create, name='contract_create'),
    path('contracts/<int:pk>/', views.contract_detail, name='contract_detail'),
    path('contracts/<int:pk>/edit/', views.contract_edit, name='contract_edit'),
    path('contracts/<int:pk>/delete/', views.contract_delete, name='contract_delete'),
    path('contracts/<int:pk>/status/<str:status>/', views.contract_status, name='contract_status'),

    # Notifications
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:pk>/read/', views.notification_read, name='notification_read'),
    path('notifications/read-all/', views.notification_read_all, name='notification_read_all'),
    path('notifications/<int:pk>/delete/', views.notification_delete, name='notification_delete'),

    path('leads/bulk-import/', views.bulk_import_leads, name='bulk_import_leads'),
    path('whatsapp/bulk/', views.bulk_whatsapp_sender, name='bulk_whatsapp_sender'),

    path('leads/<int:pk>/score/', views.score_lead_view, name='score_lead'),
    path('leads/score-all/', views.score_all_leads, name='score_all_leads'),

    path('leads/<int:pk>/ai-assign/', views.ai_assign_lead, name='ai_assign_lead'),
    path('leads/<int:pk>/next-action/', views.next_action_view, name='next_action'),

    # Sales Persons
    path('salespersons/', views.salesperson_list, name='salesperson_list'),
    path('salespersons/create/', views.salesperson_create, name='salesperson_create'),
    path('salespersons/<int:pk>/edit/', views.salesperson_edit, name='salesperson_edit'),
    path('salespersons/<int:pk>/delete/', views.salesperson_delete, name='salesperson_delete'),

    path('leads/<int:pk>/closing-probability/', views.closing_probability_view, name='closing_probability'),
    path('leads/<int:pk>/ai-message/', views.ai_followup_message_view, name='ai_followup_message'),
    path('meetings/<int:pk>/summarize/', views.ai_meeting_summary_view, name='ai_meeting_summary'),
    path('forecast/', views.sales_forecast_view, name='sales_forecast'),

    path('leads/<int:pk>/churn-risk/', views.churn_risk_view, name='churn_risk'),
    path('leads/churn-risk/all/', views.churn_risk_all_view, name='churn_risk_all'),
    path('leads/<int:pk>/upsell/', views.upsell_recommendations_view, name='upsell_recommendations'),
    path('leads/<int:pk>/lifetime-value/', views.lifetime_value_view, name='lifetime_value'),
    path('leads/<int:pk>/360/', views.customer_360_view, name='customer_360'),
    path('ceo/', views.ceo_dashboard, name='ceo_dashboard'),

    # AI Proposal Writer
    path('proposals/', views.proposal_list, name='proposal_list'),
    path('proposals/write/', views.proposal_writer, name='proposal_writer'),
    path('proposals/write/<int:lead_pk>/', views.proposal_writer, name='proposal_writer_lead'),
    path('proposals/<int:pk>/', views.proposal_detail, name='proposal_detail'),
    path('proposals/<int:pk>/delete/', views.proposal_delete, name='proposal_delete'),

    path('assistant/config/', views.assistant_config, name='assistant_config'),
    path('assistant/chat/', views.assistant_chat, name='assistant_chat'),
    path('assistant/history/<int:conversation_id>/', views.assistant_history, name='assistant_history'),

    # Emails
    path('emails/', views.email_inbox, name='email_inbox'),
    path('emails/compose/', views.email_compose, name='email_compose'),
    path('emails/compose/<int:lead_id>/', views.email_compose, name='email_compose_lead'),
    path('emails/<int:pk>/', views.email_detail, name='email_detail'),
    
    # ---- Phone calling (Twilio) ----
    path('call/phone/start/<int:lead_id>/', views.start_phone_call, name='start_phone_call'),
    path('call/phone/twiml/', views.twiml_response, name='twiml_response'),
    path('call/phone/status/<int:lead_id>/', views.call_status_callback, name='call_status_callback'),
    path('call/phone/recording/', views.recording_callback, name='recording_callback'),

    # ---- WhatsApp calling (Meta Cloud API) ----
    path('call/whatsapp/start/<int:lead_id>/', views.start_whatsapp_call, name='start_whatsapp_call'),
    path('call/whatsapp/end/<str:call_id>/', views.end_whatsapp_call, name='end_whatsapp_call'),
    path('call/whatsapp/webhook/', views.whatsapp_webhook, name='whatsapp_webhook'),

    # ---- Google Calendar ----
    path('google/authorize/', views.google_authorize, name='google_authorize'),
    path('google/callback/', views.google_callback, name='google_callback'),
    path('call/schedule/<int:lead_id>/', views.schedule_call, name='schedule_call'),
    path('call/schedule/cancel/<int:schedule_id>/', views.cancel_scheduled_call, name='cancel_scheduled_call'),
    
    # ---- Call log list----
    path('calls/', views.call_log_list, name='call_log_list'),
    path('calls/scheduled/', views.call_schedule_list, name='call_schedule_list'),
    
    ### delete bulk delete ###
    
    path('emails/<int:pk>/delete/', views.email_delete, name='email_delete'),
    path('emails/bulk-delete/', views.email_bulk_delete, name='email_bulk_delete'),

    # ── Hotels ──────────────────────────────────────────────
    path('hotels/', vt.hotel_list, name='hotel_list'),
    path('hotels/create/', vt.hotel_create, name='hotel_create'),
    path('hotels/<int:pk>/edit/', vt.hotel_edit, name='hotel_edit'),
    path('hotels/<int:pk>/delete/', vt.hotel_delete, name='hotel_delete'),
    path('hotels/reservations/', vt.hotel_reservation_list, name='hotel_reservation_list'),
    path('hotels/reservations/create/', vt.hotel_reservation_create, name='hotel_reservation_create'),
    path('hotels/reservations/<int:pk>/edit/', vt.hotel_reservation_edit, name='hotel_reservation_edit'),
    path('hotels/reservations/<int:pk>/delete/', vt.hotel_reservation_delete, name='hotel_reservation_delete'),

    # ── Suppliers ───────────────────────────────────────────
    path('suppliers/', vt.supplier_list, name='supplier_list'),
    path('suppliers/create/', vt.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/edit/', vt.supplier_edit, name='supplier_edit'),
    path('suppliers/<int:pk>/delete/', vt.supplier_delete, name='supplier_delete'),

    # ── Transportation ──────────────────────────────────────
    path('transportation/', vt.transport_list, name='transport_list'),
    path('transportation/create/', vt.transport_create, name='transport_create'),
    path('transportation/<int:pk>/edit/', vt.transport_edit, name='transport_edit'),
    path('transportation/<int:pk>/delete/', vt.transport_delete, name='transport_delete'),
    path('transportation/vehicles/', vt.vehicle_list, name='vehicle_list'),
    path('transportation/vehicles/create/', vt.vehicle_create, name='vehicle_create'),
    path('transportation/vehicles/<int:pk>/delete/', vt.vehicle_delete, name='vehicle_delete'),

    # ── Tours & Itineraries ─────────────────────────────────
    path('itineraries/', vt.itinerary_list, name='itinerary_list'),
    path('itineraries/create/', vt.itinerary_create, name='itinerary_create'),
    path('itineraries/<int:pk>/', vt.itinerary_detail, name='itinerary_detail'),
    path('itineraries/<int:pk>/edit/', vt.itinerary_edit, name='itinerary_edit'),
    path('itineraries/<int:pk>/delete/', vt.itinerary_delete, name='itinerary_delete'),
    path('itineraries/<int:itinerary_pk>/days/add/', vt.itinerary_day_add, name='itinerary_day_add'),
    path('itineraries/days/<int:pk>/delete/', vt.itinerary_day_delete, name='itinerary_day_delete'),

    # ── Corporate Travel ────────────────────────────────────
    path('corporate/requests/', vt.corporate_request_list, name='corporate_request_list'),
    path('corporate/requests/create/', vt.corporate_request_create, name='corporate_request_create'),
    path('corporate/requests/<int:pk>/status/<str:status>/', vt.corporate_request_status, name='corporate_request_status'),
    path('corporate/requests/<int:pk>/delete/', vt.corporate_request_delete, name='corporate_request_delete'),

    # ── Bulk Email ───────────────────────────────────────────
    path('bulk-email/', vt.bulk_email_list, name='bulk_email_list'),
    path('bulk-email/create/', vt.bulk_email_create, name='bulk_email_create'),
    path('bulk-email/<int:pk>/', vt.bulk_email_detail, name='bulk_email_detail'),
    path('bulk-email/<int:pk>/send/', vt.bulk_email_send, name='bulk_email_send'),
    path('bulk-email/<int:pk>/delete/', vt.bulk_email_delete, name='bulk_email_delete'),

    # ── Reviews ──────────────────────────────────────────────
    path('reviews/', vt.review_list, name='review_list'),
    path('reviews/create/', vt.review_create, name='review_create'),
    path('reviews/<int:pk>/delete/', vt.review_delete, name='review_delete'),

]
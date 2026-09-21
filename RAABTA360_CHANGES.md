# Raabta360 — Changes Summary

## 1. Bug fixes

### Positive leads Positive tab mein show nahi ho rahe the
Root cause: lead ka status **set hi nahi ho sakta tha**.
- `LeadForm` mein `status` field maujood nahi thi
- Koi `lead_edit` view hi nahi tha
- Lead list mein status badalne ka koi control nahi tha

Fix:
- `leads/forms.py` — `status` aur `spo` fields add kiye
- `leads/views.py` — naya `lead_edit` view, `update_lead_status` mein validation + ActivityLog
- `lead_list` rewrite — status tabs with live counts, `?status=` bhi support karta hai
- `lead_list.html` — har row par "Stage" dropdown se ek click mein status change
- `create_lead` ab manually chuni gayi salesperson ko overwrite nahi karta

### Follow-ups Today / Next mein show nahi ho rahe the
Root cause: **timezone mismatch**. `settings.py` mein `TIME_ZONE = 'UTC'` tha jabke aap
Asia/Karachi (UTC+5) mein hain. Code aware datetime ka `.date()` (UTC date) `timezone.localdate()`
(local date) se compare kar raha tha — dono kabhi match nahi karte the.

Fix:
- `leadcrm/settings.py` aur `leadcrm/leadcrm/settings.py` — `TIME_ZONE = 'Asia/Karachi'`
- `followup_list` rewrite — har jagah `timezone.localtime()`
- Naya **Overdue** scope (pehle purane follow-ups sirf "Pending" mein chhup jate the)
- Tabs: Pending / Overdue / Today / Upcoming / Done, sab live counts ke saath

Dono fixes automated test se verify kiye gaye (raat 1:30 ka local follow-up ab sahi
tarah "Today" mein aata hai — yehi asal bug tha).

## 2. UI redesign
- Naya design system: `static/css/raabta.css` (style.css ke BAAD load hota hai)
- Dark indigo premium sidebar, Raabta360 branding
- **Logo**: white circle hata diya. Logo ki transparent padding crop karke
  `static/images/logo_mark.png` banaya (tight round mark)
- **Dashboard** poora rewrite — hero greeting, 4 KPI cards with MoM deltas,
  6-card travel ops strip, Revenue Overview line chart, Booking Distribution donut,
  AI Lead Intelligence panel, Upcoming Departures, Today's Follow-ups, Quick Actions
- **Analytics** — bilkul nayi screen (`/analytics/`)
- Charts professional: Inter font, tabular numbers, soft gridlines, dark rounded tooltips
- Purane templates `*_legacy.html` naam se mehfooz hain

## 3. Naye modules (requirements doc se)
- **Pilgrim Management** — Pilgrim ID auto-generate, passport expiry alerts (6 month rule),
  blood group, emergency contact, room/flight/seat
- **Group / Family Management** — auto Group ID (UMR-2026-0001), leader, room allocation,
  visa & document progress
- **Document Management** — per-pilgrim, 11 document types, 6 statuses, expiry alerts
- **Profit & Cost** — `BookingCost` model: supplier cost breakdown vs selling price,
  gross profit aur margin % per booking
- **Pipeline Kanban** — stage-wise columns, AI score cards
- **Lead stages** ab doc ke mutabiq 9 hain: New, Contacted, Qualified, Positive,
  Quotation Sent, Follow-up, Booking Pending, Converted, Lost

## 4. Chalane ka tareeqa
```bash
pip install -r requirements.txt
python manage.py migrate      # migration 0033 apply karega
python manage.py runserver
```
Migration `0033` naye models banata hai aur lead status choices expand karta hai.
Purana data safe hai — maujooda status codes (new/positive/lost/quotation/converted)
waise ke waise rakhe gaye hain.

## 5. Abhi baaqi hai
- Ziyarat Management (model nahi hai)
- Flight/Transport allocation ko Pilgrim se deeply link karna
- WhatsApp templates (Quotation / Payment Reminder / Visa Update / Hotel Voucher)
- Automated notification scheduler (payment due, departure approaching, passport expiry)
- AI Sales Assistant natural-language queries

## Phase 2 — Ziyarat, Finance, and deep Pilgrim/Flight/Transport linking

### Bug fixed
`/communications/` page was throwing a 500 error:
`FieldError: Invalid field name(s) given in select_related: 'project'`.
`CommunicationLog` has no `project` field — `select_related('...', 'project')` in
`communication_list`, a dead `project_id` filter in `communication_timeline`, and an
unused Project dropdown in the log-communication form were all left over from a field
that was never added to the model. All three removed; page now returns 200.

### New: Ziyarat / Activities (`ZiyaratActivity`, `ZiyaratParticipant`)
Site name, city, date/time, duration, guide, transport link, included-vs-add-on pricing,
per-pilgrim participant assignment with attendance tracking.
URLs: `/ziyarat/`, `/ziyarat/create/`, `/ziyarat/<id>/`.

### New: Flight passenger assignment (`BookingFlight`, `BookingFlightPassenger`)
A flight leg (outbound/return) can now be assigned specific pilgrims with seat, ticket
number and baggage — not just free-text fields. Assigning a passenger keeps the
pilgrim's own `flight_number`/`seat_number` fields in sync automatically, at the model
level (`BookingFlightPassenger.save()`), so it stays correct no matter how the record
is created — through the UI, admin, or a script.
URLs: `/flights/`, `/flights/create/`, `/flights/<id>/`.

### New: Transport deep-linking
`TransportSchedule` gained a `group` FK and a `pilgrims` M2M, so a transfer can be
assigned directly to a family/group or specific pilgrims, matching the requirements
doc's "Assigned group/pilgrims" field.
URLs: `/transport/`, `/transport/create/`, `/transport/<id>/`.

### New: Finance & Commercial Management (section 11)
- `BookingInstallment` — payment schedule lines with due dates; status
  (pending/partial/paid/overdue) recalculates automatically whenever a transaction
  posts against it.
- `BookingTransaction` — actual money movement (payment or refund), with payment
  method, reference number, and an auto-generated receipt number
  (`RCPT-2026-00001`, `RFD-2026-00001`). Printable receipt page at `/receipts/<id>/`.
- `RefundRequest` — refund/cancellation requires approval before any transaction is
  created; approving auto-creates the refund transaction (no hard-delete of financial
  records, matching the doc's audit-trail requirement).
- `Booking` gained `amount_collected`, `outstanding_balance`, `payment_status`, and
  `next_due_installment` — these prefer the real transaction ledger and fall back to
  the legacy `total_received` field, so nothing already in the database breaks.
- `/receivables/` — outstanding balances with aging buckets (current / 1-30 / 31-60 /
  61-90 / 90+ days).
- `/refunds/` — approval queue.

### Testing done
- `python manage.py check` — clean.
- Full page smoke test — 24 URLs, all 200.
- End-to-end scripted flow: created a group + 2 pilgrims → assigned one to a flight
  seat → assigned one to a transport transfer → assigned one to a Ziyarat activity →
  created a booking → added an installment → recorded a payment (installment
  auto-flipped to "paid", receipt number generated, receipt page rendered) →
  submitted and approved a refund (refund transaction created, booking balance
  updated). All steps passed.
- Visually reviewed every new screen as a rendered screenshot.
- Found and fixed one real bug during testing: `BookingFlightPassenger` synced the
  pilgrim's flight/seat fields only in the view, so creating an assignment any other
  way (admin, script, future import) silently left the pilgrim record stale — moved
  the sync into the model's `save()` so it's correct regardless of the caller.

### Migrations
`0034_transportschedule_group_transportschedule_pilgrims_and_more` and
`0035_alter_bookingflight_booking`. Run `python manage.py migrate` after extracting.

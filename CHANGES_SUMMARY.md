# Holiday Express Travel CRM — Conversion Summary

This document summarizes everything changed to convert the CRM from a
software-house tool into a dedicated **travel agency CRM**, per your
requirements document.

## 1. AI Provider: Groq → OpenAI

Every AI feature now uses OpenAI instead of Groq:
- Lead scoring, churn prediction, LTV, closing probability, next-best-action,
  upsell suggestions, sales forecasting, meeting summaries, follow-up message
  drafts, proposal writer, CRM/Sales chat assistants, WhatsApp chatbot.
- Set your key as the `OPENAI_API_KEY` environment variable (same place
  `GROQ_API_KEY` used to live in your `.env`).
- Default model: `gpt-4o-mini`. Change it in the individual `ai_*.py` files
  or `chatbot/services/ai.py` / `leads/assistant/llm.py` if you want a
  different OpenAI model.
- `requirements.txt` now lists `openai` instead of `groq`.

## 2. Removed — Software House Features

These were project-management / IT-helpdesk features that don't belong in a
travel agency CRM. Fully removed (models, views, URLs, admin, templates,
sidebar links, dashboard widgets):
- **Projects, Milestones, Tasks** (software project tracking)
- **Support Tickets** (IT helpdesk tickets)

`GeneralTask` (day-to-day follow-up tasks/reminders) was **kept** — that's a
normal CRM task list, not a software-project task.

## 3. Added — Travel Agency Modules

All of these are new models + full CRUD (list/create/edit/delete) + sidebar
links, built to match your requirements document:

| Module | What it covers |
|---|---|
| **Hotels** | Hotel master catalog (name, city, star rating, contact) + Hotel Reservations (room type, meal plan, check-in/out, nights, rate, confirmation #, cancellation policy) |
| **Suppliers** | Airlines, hotels, transport providers, visa partners, other vendors — with rates/contact notes |
| **Transportation** | Vehicles (fleet/contracted) + Transport Schedule (airport pickup/drop-off, full-day car, driver, vehicle, pickup/drop-off locations, status) |
| **Tours & Itineraries** | Itinerary header (group/private/customized/honeymoon/corporate/sightseeing) + **day-by-day builder** (activities, meals, hotel, flight, instructions per day) |
| **Corporate Travel** | Corporate Travel Requests — employee, purpose, destination, dates, estimated cost, corporate rate flag, approve/reject workflow, linked to your existing Company/Contact (Corporate Accounts / Employee Travelers) |
| **Bulk Email** | Campaign builder with audience segmentation (by destination, trip type, lead status, country), recipient list, and a Send action that reports delivered/failed counts — separate from your existing one-to-one email |
| **Reviews & Feedback** | Star rating + comment per customer/booking, with a public/private flag |

## 4. Already Present — No Rebuild Needed

Good news: your existing codebase already covered a lot of ground, so these
requirements were **not** rebuilt from scratch:
- **Umrah/Hajj Management** — the `Package` model already has deep Hajj/Umrah
  fields: Hijri dates, Makkah/Madinah/Azizia room sharing breakdowns, maktab
  details, Mina category, itinerary images for each ritual day.
- **Visa Management** — `VisaApplication` + `VisaDocumentChecklistItem`
  already cover country/type, fees, processing time, status, appointments,
  approvals/rejections, and a missing-document checklist.
- **Document Management** — `Document` model with type, expiry, lead/booking
  attachment already existed.
- **Payments & Invoices** — `Payment`, `ScheduledPayment`, `Installment`
  already existed.
- **WhatsApp** — chatbot app + bulk WhatsApp sender already existed.
- **Tasks & Follow-ups** — `FollowUp` and `GeneralTask` already existed.
- **Reports & Analytics, AI Intelligence** — already extensive (lead scoring,
  churn, LTV, forecasting, next-best-action, upsell, meeting summaries).

## 5. Sidebar Reorganized

- **TRAVEL OPERATIONS**: Bookings, Packages (Hajj/Umrah), Visa Applications,
  Hotels, Transportation, Tours & Itineraries
- **CORPORATE CLIENTS**: Corporate Accounts, Employee Travelers, Corporate
  Travel Requests, Suppliers
- **EMAILS**: All Emails, Compose, **Bulk Email Campaigns**
- **REVIEWS & FEEDBACK**: Customer Reviews
- Removed: PROJECTS section, SUPPORT TICKETS section

## 6. Permissions

Added new permission toggles (full/view/none per user) for: `hotels`,
`transportation`, `itineraries`, `suppliers`, `corporate`, `bulk_email`,
`reviews`. Removed the old `projects` and `support` toggles. Manage these
the same way you already manage other section permissions (per-user, in the
Users admin area).

## 7. Setup Notes

1. Set `OPENAI_API_KEY` in your environment (`.env` file, same as before).
2. Run migrations: `python manage.py migrate`
   (one new migration: `leads/migrations/0032_hotel_supplier_remove_task_milestone_and_more.py`)
3. Install the updated requirements: `pip install -r requirements.txt`
4. The new modules are simple, functional CRUD screens styled to match your
   existing UI. If you want richer detail pages (e.g., a hotel detail page
   with all its past reservations, or nicer itinerary PDF export), those can
   be layered on top later — the data model is already there to support it.

## 8. Known Limitations / Next Steps

- Bulk email sending uses Django's configured email backend (same one your
  one-to-one email already uses) — no separate ESP integration (e.g.
  SendGrid/Mailgun) was added. For large campaigns you may want to move
  sending to a background task queue (Celery) instead of the synchronous
  loop currently used.
- Itinerary PDF/branded export was not built — currently it's an in-CRM
  builder only.
- Corporate "credit and billing" tracking is a simple estimated-cost field
  today; a full credit-limit/running-balance ledger per corporate account
  was not built (can be added on top of the existing Payment/Invoice models).

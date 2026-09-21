import imaplib
import email
from email.header import decode_header
from django.core.management.base import BaseCommand
from django.conf import settings
from leads.models import EmailLog, UserProfile


def _decode(value):
    if not value:
        return ''
    parts = decode_header(value)
    decoded = ''
    for text, enc in parts:
        if isinstance(text, bytes):
            decoded += text.decode(enc or 'utf-8', errors='ignore')
        else:
            decoded += text
    return decoded


class Command(BaseCommand):
    help = 'Fetch new inbound emails via IMAP for all configured accounts'

    def handle(self, *args, **options):
        for key, account in settings.EMAIL_ACCOUNTS.items():
            if not account.get('IMAP_HOST'):
                continue
            self.fetch_for_account(key, account)

    def fetch_for_account(self, account_key, account):
        try:
            imap = imaplib.IMAP4_SSL(account['IMAP_HOST'], account['IMAP_PORT'])
            imap.login(account['HOST_USER'], account['HOST_PASSWORD'])
            imap.select('INBOX')

            status, msg_ids = imap.search(None, 'UNSEEN')
            if status != 'OK':
                return

            for msg_id in msg_ids[0].split():
                status, msg_data = imap.fetch(msg_id, '(RFC822)')
                if status != 'OK':
                    continue
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                subject = _decode(msg.get('Subject'))
                from_email = email.utils.parseaddr(msg.get('From'))[1]

                body = ''
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == 'text/plain' and not part.get('Content-Disposition'):
                            body = part.get_payload(decode=True).decode(
                                part.get_content_charset() or 'utf-8', errors='ignore'
                            )
                            break
                else:
                    body = msg.get_payload(decode=True).decode(
                        msg.get_content_charset() or 'utf-8', errors='ignore'
                    )

                # find CRM user who owns this mailbox, so message shows under them
                sent_by = None
                profile = UserProfile.objects.filter(email_account_key=account_key).first()
                if profile:
                    sent_by = profile.user

                EmailLog.objects.create(
                    to_email=account['HOST_USER'],
                    from_email=from_email,
                    subject=subject or '(no subject)',
                    message=body,
                    status='sent',
                    direction='inbound',
                    account_key=account_key,
                    sent_by=sent_by,
                )

            imap.logout()
            self.stdout.write(self.style.SUCCESS(f'Fetched inbound emails for {account_key}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'IMAP fetch failed for {account_key}: {e}'))
import asyncio
import smtplib
import urllib.request
import json
import base64
import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

logger = logging.getLogger("email_service")

def _send_via_resend_http(api_key: str, to_email: str, subject: str, body_html: str, from_email: str) -> bool:
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json"
    }
    # Resend testing sender requirement
    sender = "onboarding@resend.dev"
    payload = {
        "from": sender,
        "to": [to_email],
        "subject": subject,
        "html": body_html
    }
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=12) as resp:
            if resp.status in (200, 201):
                print(f"✅ Email delivered to {to_email} via Resend HTTP API (Port 443 HTTPS)!")
                return True
    except urllib.error.HTTPError as http_err:
        try:
            err_body = http_err.read().decode('utf-8')
            print(f"Notice on Resend HTTP API ({http_err.code}): {err_body}")
            # If in sandbox mode and recipient is unverified, forward to the verified account
            if http_err.code == 403 and "own email address" in err_body:
                import re
                match = re.search(r'\(([^)]+@[^)]+)\)', err_body)
                allowed_email = match.group(1) if match else os.getenv("SMTP_USER")
                if allowed_email and allowed_email != to_email:
                    print(f"🔄 Resend Sandbox: Forwarding ticket confirmation to verified inbox ({allowed_email})...")
                    payload["to"] = [allowed_email]
                    payload["subject"] = f"[For {to_email}] {subject}"
                    data = json.dumps(payload).encode('utf-8')
                    req2 = urllib.request.Request(url, data=data, headers=headers, method="POST")
                    with urllib.request.urlopen(req2, timeout=12) as resp2:
                        if resp2.status in (200, 201):
                            print(f"✅ Email successfully delivered to verified inbox ({allowed_email}) via Resend HTTPS API!")
                            return True
        except Exception as retry_err:
            print(f"Resend sandbox retry notice: {retry_err}")
    except Exception as e:
        print(f"Notice on Resend HTTP API dispatch: {e}")
    return False

def _send_via_brevo_http(api_key: str, to_email: str, subject: str, body_html: str, from_email: str) -> bool:
    try:
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "api-key": api_key.strip(),
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        sender_email = from_email if ("@" in from_email and "gmail.com" not in from_email) else "tickets@booking-platform.com"
        payload = {
            "sender": {"name": "Ticketsmith Platform", "email": sender_email},
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": body_html
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=12) as resp:
            if resp.status in (200, 201):
                print(f"✅ Email delivered to {to_email} via Brevo HTTP API (Port 443 HTTPS)!")
                return True
    except urllib.error.HTTPError as http_err:
        try:
            err_body = http_err.read().decode('utf-8')
            print(f"Notice on Brevo HTTP API ({http_err.code}): {err_body}")
        except Exception:
            print(f"Notice on Brevo HTTP API: {http_err}")
    except Exception as e:
        print(f"Notice on Brevo HTTP API dispatch: {e}")
    return False

def _send_via_mailersend_http(api_key: str, to_email: str, subject: str, body_html: str, from_email: str) -> bool:
    try:
        url = "https://api.mailersend.com/v1/email"
        headers = {
            "Authorization": f"Bearer {api_key.strip()}",
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        }
        sender_email = from_email if ("@" in from_email and "gmail.com" not in from_email) else "info@trial-custom.mlsender.net"
        payload = {
            "from": {"email": sender_email, "name": "Ticketsmith Platform"},
            "to": [{"email": to_email, "name": "Ticket Customer"}],
            "subject": subject,
            "html": body_html
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=12) as resp:
            if resp.status in (200, 201, 202):
                print(f"✅ Email delivered to {to_email} via MailerSend HTTP API (Port 443 HTTPS)!")
                return True
    except urllib.error.HTTPError as http_err:
        try:
            err_body = http_err.read().decode('utf-8')
            print(f"Notice on MailerSend HTTP API ({http_err.code}): {err_body}")
        except Exception:
            print(f"Notice on MailerSend HTTP API: {http_err}")
    except Exception as e:
        print(f"Notice on MailerSend HTTP API dispatch: {e}")
    return False

def _sync_send_email(
    to_email: str,
    subject: str,
    body_html: str,
    qr_code_b64: str = None
) -> bool:
    print("\n=======================================================")
    print(f"📧 [EMAIL SERVICE] Recipient: {to_email}")
    print(f"📌 Subject: {subject}")

    resend_key = os.getenv("RESEND_API_KEY", "").strip()
    brevo_key = os.getenv("BREVO_API_KEY", "").strip()
    mailersend_key = os.getenv("MAILERSEND_API_KEY", "").strip()

    # 1. Try MailerSend / MailerLite HTTP API over HTTPS (Port 443)
    if mailersend_key:
        print("🚀 Attempting dispatch via MailerSend HTTP API (HTTPS Port 443)...")
        if _send_via_mailersend_http(mailersend_key, to_email, subject, body_html, os.getenv("SMTP_FROM", "")):
            print("=======================================================\n")
            return True

    # 2. Try Resend HTTP API over HTTPS (Port 443)
    if resend_key:
        print("🚀 Attempting dispatch via Resend HTTP API (HTTPS Port 443)...")
        if _send_via_resend_http(resend_key, to_email, subject, body_html, os.getenv("SMTP_FROM", "")):
            print("=======================================================\n")
            return True

    # 3. Try Brevo HTTP API over HTTPS (Port 443)
    if brevo_key:
        print("🚀 Attempting dispatch via Brevo HTTP API (HTTPS Port 443)...")
        if _send_via_brevo_http(brevo_key, to_email, subject, body_html, os.getenv("SMTP_FROM", "")):
            print("=======================================================\n")
            return True
            return True

    # 3. Fallback to Direct SMTP (Port 587 TLS / Port 465 SSL)
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_pass = os.getenv("SMTP_PASS", "").strip().replace(" ", "")
    smtp_from = os.getenv("SMTP_FROM", smtp_user).strip() or smtp_user

    if not smtp_user or not smtp_pass:
        print("⚠️ [EMAIL NOTICE] SMTP credentials not configured. Set RESEND_API_KEY or SMTP_USER/SMTP_PASS in Render Environment Variables.")
        print("=======================================================\n")
        return False

    try:
        msg = MIMEMultipart("related")
        msg["Subject"] = subject
        msg["From"] = smtp_from
        msg["To"] = to_email

        msg_alt = MIMEMultipart("alternative")
        msg.attach(msg_alt)

        html_content = body_html
        if qr_code_b64 and "cid:qrcode_image" not in body_html:
            html_content += '<br/><br/><h3>Your Official Digital Ticket Pass:</h3><img src="cid:qrcode_image" alt="QR Ticket" style="max-width:240px;border-radius:12px;border:2px solid #6366f1;"/>'

        msg_alt.attach(MIMEText(html_content, "html"))

        if qr_code_b64:
            try:
                raw_b64 = qr_code_b64.split(",")[-1] if "," in qr_code_b64 else qr_code_b64
                img_bytes = base64.b64decode(raw_b64)
                img = MIMEImage(img_bytes)
                img.add_header("Content-ID", "<qrcode_image>")
                img.add_header("Content-Disposition", "inline", filename="ticket_qr.png")
                msg.attach(img)
            except Exception as qr_err:
                logger.warning(f"CID QR image attachment notice: {qr_err}")

        # Attempt Port 587 (TLS)
        try:
            with smtplib.SMTP(smtp_host, 587, timeout=12) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_from, [to_email], msg.as_string())
            print(f"✅ Delivered to ({to_email}) via Port 587 TLS!")
            print("=======================================================\n")
            return True
        except Exception as err587:
            print(f"Notice: Port 587 TLS notice ({err587}). Attempting Port 465 SSL fallback...")
            # Attempt Port 465 (SSL Fallback)
            with smtplib.SMTP_SSL(smtp_host, 465, timeout=12) as server:
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_from, [to_email], msg.as_string())
            print(f"✅ Delivered to ({to_email}) via Port 465 SSL!")
            print("=======================================================\n")
            return True

    except Exception as e:
        err_str = str(e)
        if "101" in err_str or "unreachable" in err_str.lower():
            print("=======================================================")
            print("❌ RENDER CLOUD FIREWALL NOTICE:")
            print("Render Free Tier blocks outbound SMTP socket ports (587 / 465).")
            print("To enable instant live email delivery on Render Free Tier:")
            print("1. Get a free key from resend.com or brevo.com (100% free - 3,000 emails/mo).")
            print("2. Add `RESEND_API_KEY` or `BREVO_API_KEY` in Render Environment Variables.")
            print("HTTPS API requests run on Port 443, which is 100% allowed on Render!")
            print("=======================================================\n")
        else:
            print(f"❌ SMTP delivery error for {to_email}: {e}")
            print("=======================================================\n")
        logger.error(f"SMTP delivery error for {to_email}: {e}")
        return False

async def send_email_notification(
    to_email: str,
    subject: str,
    body_html: str,
    qr_code_b64: str = None
) -> bool:
    return await asyncio.to_thread(_sync_send_email, to_email, subject, body_html, qr_code_b64)

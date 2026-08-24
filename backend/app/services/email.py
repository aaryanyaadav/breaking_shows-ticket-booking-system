import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import base64
import logging
import os

logger = logging.getLogger("email_service")

def _sync_send_email(
    to_email: str,
    subject: str,
    body_html: str,
    qr_code_b64: str = None
) -> bool:
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_pass = os.getenv("SMTP_PASS", "").strip().replace(" ", "")
    smtp_from = os.getenv("SMTP_FROM", smtp_user).strip() or smtp_user

    print("\n=======================================================")
    print(f"📧 [EMAIL SERVICE] Recipient: {to_email}")
    print(f"📧 [EMAIL SERVICE] Sender: {smtp_from} (User: {smtp_user})")
    print(f"📌 Subject: {subject}")

    if not smtp_user or not smtp_pass:
        print("⚠️ [EMAIL NOTICE] SMTP_USER or SMTP_PASS environment variable is missing on cloud server.")
        print("Please configure SMTP_USER and SMTP_PASS in your Render Environment Variables tab.")
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

        # Embed QR Code as MIME CID Inline Image Attachment
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

        # Attempt 1: Port 587 (TLS)
        try:
            with smtplib.SMTP(smtp_host, 587, timeout=15) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_from, [to_email], msg.as_string())
            print(f"✅ Real Email successfully delivered to ({to_email}) via Port 587 TLS!")
            print("=======================================================\n")
            logger.info(f"Real Email dispatched to {to_email} via Port 587 TLS")
            return True
        except Exception as err587:
            print(f"Notice: Port 587 TLS notice ({err587}). Attempting Port 465 SSL fallback...")
            # Attempt 2: Port 465 (SSL Fallback)
            with smtplib.SMTP_SSL(smtp_host, 465, timeout=15) as server:
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_from, [to_email], msg.as_string())
            print(f"✅ Real Email successfully delivered to ({to_email}) via Port 465 SSL!")
            print("=======================================================\n")
            logger.info(f"Real Email dispatched to {to_email} via Port 465 SSL")
            return True

    except Exception as e:
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
    """
    Non-blocking async wrapper around dual-port SMTP email dispatch.
    """
    return await asyncio.to_thread(_sync_send_email, to_email, subject, body_html, qr_code_b64)

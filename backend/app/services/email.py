import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import base64
import logging
import os

logger = logging.getLogger("email_service")

async def send_email_notification(
    to_email: str,
    subject: str,
    body_html: str,
    qr_code_b64: str = None
):
    """
    Email Notification Service.
    1. Always logs structured dispatch to server console.
    2. Sends real email to inbox if SMTP_USER and SMTP_PASS environment variables are configured.
    """
    print("\n=======================================================")
    print(f"📧 [EMAIL SERVICE] Dispatching to: {to_email}")
    print(f"📌 Subject: {subject}")
    print("-------------------------------------------------------")
    print(f"Body snippet: {body_html[:200]}...")
    if qr_code_b64:
        print(f"🎟️ QR Code Ticket Pass attached (Base64 len: {len(qr_code_b64)})")
    print("=======================================================\n")

    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_pass = os.getenv("SMTP_PASS", "").strip()
    smtp_from = os.getenv("SMTP_FROM", smtp_user).strip() or smtp_user

    if not smtp_user or not smtp_pass:
        logger.info(f"SMTP credentials not configured. Email logged to console/DB for {to_email}.")
        return True

    try:
        msg = MIMEMultipart("related")
        msg["Subject"] = subject
        msg["From"] = smtp_from
        msg["To"] = to_email

        msg_alt = MIMEMultipart("alternative")
        msg.attach(msg_alt)

        html_content = body_html
        if qr_code_b64 and "cid:qrcode" not in body_html:
            html_content += f'<br/><br/><h3>Your Ticket QR Pass:</h3><img src="{qr_code_b64}" alt="QR Ticket" style="max-width:240px;"/>'

        msg_alt.attach(MIMEText(html_content, "html"))

        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10) as server:
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_from, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_from, [to_email], msg.as_string())

        print(f"✅ Real Email delivered to dynamic user inbox ({to_email}) via SMTP ({smtp_host}:{smtp_port})!")
        logger.info(f"Real Email dispatched to {to_email}")
        logger.info(f"Real Email dispatched to {to_email}")
    except Exception as e:
        print(f"⚠️ SMTP delivery error: {e}")
        logger.error(f"SMTP delivery error for {to_email}: {e}")

    return True

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
    Email Notification Service with MIME CID inline QR attachments & Gmail SMTP delivery.
    """
    print("\n=======================================================")
    print(f"📧 [EMAIL SERVICE] Dispatching to recipient: {to_email}")
    print(f"📌 Subject: {subject}")
    print("-------------------------------------------------------")
    print(f"Body snippet: {body_html[:200]}...")
    if qr_code_b64:
        print(f"🎟️ QR Code Ticket Pass attached (Base64 len: {len(qr_code_b64)})")
    print("=======================================================\n")

    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "projects.aky@gmail.com").strip()
    smtp_pass = os.getenv("SMTP_PASS", "ynsy xxbp iacu ofuo").strip()
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
        if qr_code_b64 and "cid:qrcode_image" not in body_html:
            html_content += '<br/><br/><h3>Your Official Digital Ticket Pass:</h3><img src="cid:qrcode_image" alt="QR Ticket" style="max-width:240px;border-radius:12px;border:2px solid #6366f1;"/>'

        msg_alt.attach(MIMEText(html_content, "html"))

        # Embed QR Code as MIME CID Inline Image Attachment for full Gmail/Outlook/Apple Mail support
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

        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as server:
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_from, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_from, [to_email], msg.as_string())

        print(f"✅ Real Email successfully delivered to user inbox ({to_email}) via Gmail SMTP!")
        logger.info(f"Real Email dispatched to {to_email}")
    except Exception as e:
        print(f"⚠️ SMTP delivery error for {to_email}: {e}")
        logger.error(f"SMTP delivery error for {to_email}: {e}")

    return True

import os
import smtplib
from email.message import EmailMessage


def send_pdf(settings, recipient, subject, body, report_path):
    if not settings.email_address or not settings.email_app_password:
        return False, "Email credentials are not configured."

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.email_address
    message["To"] = recipient
    message.set_content(body)

    with open(report_path, "rb") as handle:
        message.add_attachment(
            handle.read(),
            maintype="application",
            subtype="pdf",
            filename=os.path.basename(report_path),
        )

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(settings.email_address, settings.email_app_password)
            server.send_message(message)
        return True, None
    except Exception as exc:
        return False, str(exc)

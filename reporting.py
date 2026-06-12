import os
import smtplib
import re
from email.message import EmailMessage
from fpdf import FPDF
from dotenv import load_dotenv

load_dotenv()
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_APP_PASSWORD = os.getenv('EMAIL_APP_PASSWORD')

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, self.title, 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_pdf(content, filename, report_title):
    """Creates a PDF file from the given content string."""
    pdf = PDF()
    pdf.title = report_title
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Normalize unsupported unicode for core fonts.
    content = content.encode("latin-1", "replace").decode("latin-1")

    lines = content.splitlines()
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            pdf.ln(2)
            continue

        # Section headings like "Overview:" or markdown headings.
        if line.startswith("#"):
            heading = line.lstrip("#").strip()
            pdf.set_font("Arial", "B", 11)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 7, txt=heading)
            pdf.ln(1)
            continue
        # Uppercase section heading support (e.g., "MARKET REGIME SNAPSHOT:")
        if re.fullmatch(r"[A-Z0-9/\-\(\)\s,&]+:?", line) and len(line) <= 100:
            heading_text = line if line.endswith(":") else f"{line}:"
            pdf.set_font("Arial", "B", 10)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 6, txt=heading_text)
            pdf.ln(1)
            continue
        if line.endswith(":") and len(line) <= 80:
            pdf.set_font("Arial", "B", 10)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 6, txt=line)
            pdf.ln(1)
            continue

        # Bullet support.
        if line.startswith("- ") or line.startswith("* "):
            bullet_text = f"- {line[2:].strip()}"
            pdf.set_font("Arial", "", 9)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 6, txt=bullet_text)
            continue

        pdf.set_font("Arial", "", 9)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 6, txt=line)

    pdf.output(filename)
    return filename

def send_email(subject, body, attachment_path, recipient):
    """Sends an email with a PDF attachment using Gmail SMTP."""
    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = recipient
        msg.set_content(body)

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, 'rb') as f:
                pdf_data = f.read()
            msg.add_attachment(pdf_data, maintype='application', subtype='pdf', filename=os.path.basename(attachment_path))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
            server.send_message(msg)
        print(f"Email sent successfully to {recipient} with subject '{subject}'")
        return True, None
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False, str(e)

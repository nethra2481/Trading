import os
from datetime import datetime

from fpdf import FPDF


class ReportPDF(FPDF):
    def __init__(self, title):
        super().__init__()
        self.report_title = title

    def header(self):
        self.set_font("Helvetica", "B", 13)
        self.multi_cell(0, 7, self.report_title, align="C")
        self.ln(4)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "", 8)
        self.cell(0, 8, f"Page {self.page_no()} | Educational analysis only", align="C")


def create_pdf(title, body, category):
    os.makedirs("reports", exist_ok=True)
    filename = f"{category}_Analysis_{datetime.now().strftime('%Y-%m-%d_%H%M')}.pdf"
    path = os.path.abspath(os.path.join("reports", filename))

    pdf = ReportPDF(title)
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()
    safe_body = body.encode("latin-1", "replace").decode("latin-1")

    for raw_line in safe_body.splitlines():
        line = raw_line.strip()
        if not line:
            pdf.ln(2)
            continue
        pdf.set_x(pdf.l_margin)
        if line.endswith(":") and line.upper() == line:
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(0, 6, line)
        else:
            pdf.set_font("Helvetica", "", 9)
            pdf.multi_cell(0, 5.5, line)

    pdf.output(path)
    return filename, path

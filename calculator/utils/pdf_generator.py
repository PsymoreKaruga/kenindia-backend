# backend/calculator/utils/pdf_generator.py
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime
import os
from io import BytesIO

# --- CONFIG ---
COMPANY_NAME = "Kenindia Assurance Company Limited"
ADDRESS = "Kenindia House, Loita Street, P.O. Box 44371-00100, Nairobi"
PHONE = "+254 20 222 0000"
EMAIL = "info@kenindia.com"
LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "static", "logo.png")  # Update path

styles = getSampleStyleSheet()
# Add custom styles if they don't already exist in the sample stylesheet.
try:
    styles.add(ParagraphStyle(name="Center", alignment=TA_CENTER, fontSize=12, leading=14))
except Exception:
    pass

try:
    styles.add(ParagraphStyle(name="Right", alignment=TA_RIGHT, fontSize=10))
except Exception:
    pass

try:
    styles.add(ParagraphStyle(name="Bold", fontSize=11, fontName="Helvetica-Bold"))
except Exception:
    pass

try:
    styles.add(ParagraphStyle(name="Italic", fontSize=9, fontName="Helvetica-Oblique", textColor=colors.grey))
except Exception:
    pass

def format_currency(value):
    return f"KSh {value:,.2f}"

def create_pdf(data, filename="quotation.pdf"):
    """Create a PDF file at `filename` from the provided `data` dict.

    For server-side streaming, prefer `render_pdf_to_bytes(data)` which returns bytes.
    """
    doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []

    # --- Header ---
    if os.path.exists(LOGO_PATH):
        logo = Image(LOGO_PATH, width=1.2*inch, height=0.6*inch)
        logo.hAlign = 'LEFT'
    else:
        logo = Paragraph("[[ LOGO ]]", styles["Center"])

    header_table = Table([
        [logo, Paragraph(f"<font size=14><b>{COMPANY_NAME}</b></font><br/>{ADDRESS}<br/>Tel: {PHONE} | {EMAIL}", styles["Normal"])],
    ], colWidths=[1.5*inch, 4.5*inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.3*inch))

    # --- Title ---
    story.append(Paragraph("LIFE INSURANCE QUOTATION", styles["Title"]))
    story.append(Paragraph(f"Issued on: {datetime.now().strftime('%d %B %Y')}", styles["Italic"]))
    story.append(Spacer(1, 0.2*inch))

    # --- Client Details ---
    client_data = [
        ["Product", data["product"].replace("_", " ").title()],
        ["Name", "Parent (Policyholder)"],
        ["Date of Birth", data.get("dob", "N/A")],
        ["Age Next Birthday", data.get("ageNextBirthday", "N/A")],
        ["Gender", data["gender"].capitalize()],
        ["Payment Mode", data["mode"].capitalize()],
        ["Term", f"{data['term']} years"],
    ]
    if data["product"] in ["money_back_15", "money_back_10"]:
        client_data.append(["Minimum Sum Assured", "KSh 50,000"])
    elif data["product"] == "academic_advantage":
        client_data.append(["Minimum Sum Assured", "KSh 100,000"])

    client_table = Table(client_data, colWidths=[2*inch, 3.5*inch])
    client_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(client_table)
    story.append(Spacer(1, 0.3*inch))


def render_pdf_to_bytes(data):
    """Render the same PDF into bytes (BytesIO) so it can be returned from Django views.

    This function builds the document into an in-memory buffer and returns the bytes.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5 * inch, bottomMargin=0.5 * inch)
    story = []

    # --- Header ---
    if os.path.exists(LOGO_PATH):
        logo = Image(LOGO_PATH, width=1.2 * inch, height=0.6 * inch)
        logo.hAlign = 'LEFT'
    else:
        logo = Paragraph("[[ LOGO ]]", styles["Center"])

    header_table = Table([
        [logo, Paragraph(f"<font size=14><b>{COMPANY_NAME}</b></font><br/>{ADDRESS}<br/>Tel: {PHONE} | {EMAIL}", styles["Normal"])],
    ], colWidths=[1.5 * inch, 4.5 * inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.3 * inch))

    # --- Title ---
    story.append(Paragraph("LIFE INSURANCE QUOTATION", styles["Title"]))
    story.append(Paragraph(f"Issued on: {datetime.now().strftime('%d %B %Y')}", styles["Italic"]))
    story.append(Spacer(1, 0.2 * inch))

    # Client details
    client_data = [
        ["Product", data.get("product", "").replace("_", " ").title()],
        ["Name", data.get("customerName") or data.get("input", {}).get("name") or "Parent (Policyholder)"],
        ["Date of Birth", data.get("input", {}).get("dob", "N/A")],
        ["Age Next Birthday", data.get("input", {}).get("ageNextBirthday", "N/A")],
        ["Gender", (data.get("input", {}).get("gender") or "").capitalize()],
        ["Payment Mode", (data.get("input", {}).get("mode") or "").capitalize()],
        ["Term", f"{data.get('input', {}).get('term', '')} years"],
    ]
    client_table = Table(client_data, colWidths=[2 * inch, 3.5 * inch])
    client_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(client_table)
    story.append(Spacer(1, 0.3 * inch))

    # Premium breakdown
    results = data.get("results") or {}
    sa = results.get("estimated_sum_assured") or data.get("input", {}).get("sumAssured")
    premium_data = [["Description", "Amount (KSh)"], ["Sum Assured", format_currency(sa)], ["Basic Premium", format_currency(results.get("basic_premium", 0))]]
    if results.get("dab", 0) > 0:
        premium_data.append(["Double Accident Benefit (DAB)", format_currency(results.get("dab"))])
    if results.get("wp", 0) > 0:
        premium_data.append(["Waiver of Premium (WP)", format_currency(results.get("wp"))])

    premium_table = Table(premium_data, colWidths=[3.5 * inch, 2.5 * inch])
    premium_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f6fb')),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(premium_table)
    story.append(Spacer(1, 0.3 * inch))

    # Benefits
    if isinstance(results.get("benefits"), dict):
        benefits_table_data = [["Benefit", "Amount (KSh)"]]
        for k, v in results.get("benefits").items():
            benefits_table_data.append([k, format_currency(v)])
        benefits_table = Table(benefits_table_data, colWidths=[3.5 * inch, 2.5 * inch])
        benefits_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f6fb')),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(Paragraph("Benefits", styles["Heading3"]))
        story.append(benefits_table)

    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("This quotation is indicative and subject to underwriting. For official confirmation contact Kenindia Assurance.", styles["Italic"]))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
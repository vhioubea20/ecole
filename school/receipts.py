from io import BytesIO
from pathlib import Path

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen import canvas


BLUE = colors.HexColor("#1a486c")
INK = colors.HexColor("#172229")
MUTED = colors.HexColor("#63727c")
PALE = colors.HexColor("#e8f2f7")


def _format_amount(amount):
    return f"{amount:,.2f}".replace(",", " ").replace(".", ",") + " GNE"


def build_payment_receipt(payment):
    output = BytesIO()
    page_width, page_height = A5
    document = canvas.Canvas(output, pagesize=A5)
    document.setTitle(f"Reçu de paiement {payment.pk}")
    document.setAuthor("Gestion scolaire")

    margin = 38
    top = page_height - 38
    logo_path = Path(settings.BASE_DIR) / "image" / "PKF Solution OK.png"
    if logo_path.exists():
        document.drawImage(
            ImageReader(str(logo_path)),
            margin,
            top - 47,
            width=54,
            height=47,
            preserveAspectRatio=True,
            anchor="c",
            mask="auto",
        )

    document.setFillColor(MUTED)
    document.setFont("Helvetica", 9)
    document.drawString(margin + 66, top - 14, "GESTION SCOLAIRE")
    document.setFillColor(BLUE)
    document.setFont("Helvetica-Bold", 18)
    document.drawString(margin + 66, top - 36, "REÇU DE PAIEMENT")
    document.setStrokeColor(BLUE)
    document.setLineWidth(2)
    document.line(margin, top - 61, page_width - margin, top - 61)

    document.setFillColor(INK)
    document.setFont("Helvetica-Bold", 10)
    document.drawString(margin, top - 85, f"Reçu N° RCPT-{payment.pk:06d}")
    document.setFont("Helvetica", 10)
    document.drawRightString(page_width - margin, top - 85, f"Date : {payment.date_paiement:%d/%m/%Y}")

    panel_top = top - 108
    panel_height = 225
    document.setFillColor(PALE)
    document.roundRect(margin, panel_top - panel_height, page_width - 2 * margin, panel_height, 8, fill=1, stroke=0)

    student = payment.student
    rows = [
        ("Matricule", student.matricule),
        ("Élève", f"{student.first_name} {student.last_name}"),
        ("Classe", student.school_class.libelle),
        ("Date du paiement", payment.date_paiement.strftime("%d/%m/%Y")),
    ]
    row_y = panel_top - 30
    for label, value in rows:
        document.setFillColor(MUTED)
        document.setFont("Helvetica", 9)
        document.drawString(margin + 18, row_y, label.upper())
        document.setFillColor(INK)
        document.setFont("Helvetica-Bold", 12)
        value_lines = simpleSplit(str(value), "Helvetica-Bold", 12, page_width - 2 * margin - 36)
        for line_index, line in enumerate(value_lines[:2]):
            document.drawString(margin + 18, row_y - 18 - (line_index * 15), line)
        row_y -= 48 if len(value_lines) > 1 else 42

    amount_y = panel_top - panel_height - 48
    document.setFillColor(MUTED)
    document.setFont("Helvetica", 10)
    document.drawString(margin, amount_y, "MONTANT REÇU (GNE)")
    document.setFillColor(BLUE)
    document.setFont("Helvetica-Bold", 23)
    document.drawRightString(page_width - margin, amount_y - 2, _format_amount(payment.montant))
    document.setStrokeColor(colors.HexColor("#dce4e7"))
    document.setLineWidth(0.8)
    document.line(margin, amount_y - 14, page_width - margin, amount_y - 14)

    signature_y = amount_y - 78
    document.setFillColor(INK)
    document.setFont("Helvetica", 10)
    document.drawString(margin, signature_y, "Signature et cachet du responsable")
    document.setStrokeColor(MUTED)
    document.line(page_width - margin - 145, signature_y - 20, page_width - margin, signature_y - 20)
    document.setFillColor(MUTED)
    document.setFont("Helvetica", 8)
    document.drawCentredString(page_width / 2, 24, "Conservez ce reçu comme justificatif de paiement.")

    document.showPage()
    document.save()
    return output.getvalue()
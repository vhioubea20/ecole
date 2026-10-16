from datetime import date
from decimal import Decimal

from django.utils import timezone

from .models import SchoolFee

MONTH_LABELS = {
    10: "Octobre",
    11: "Novembre",
    12: "Décembre",
    1: "Janvier",
    2: "Février",
    3: "Mars",
    4: "Avril",
    5: "Mai",
    6: "Juin",
}


def fee_annual_amount(fee):
    if fee is None:
        return Decimal("0.00")
    if fee.nature == SchoolFee.Nature.TUITION and fee.mode == SchoolFee.Mode.MONTHLY:
        return fee.montant * 9
    return fee.montant


def monthly_due_schedule(tuition_fee):
    tuition_annual = fee_annual_amount(tuition_fee)
    monthly_tuition = (
        tuition_fee.montant
        if tuition_fee and tuition_fee.mode == SchoolFee.Mode.MONTHLY
        else (tuition_annual / 9).quantize(Decimal("0.01"))
    )
    dues = [monthly_tuition] * 9
    dues[-1] += tuition_annual - sum(dues, Decimal("0.00"))
    return dues


def school_year_data(reference_date=None):
    reference_date = reference_date or timezone.localdate()
    start_year = reference_date.year if reference_date.month >= 9 else reference_date.year - 1
    period_start = date(start_year, 9, 1)
    period_end = date(start_year + 1, 9, 1)
    months = []

    for month in (10, 11, 12, 1, 2, 3, 4, 5, 6):
        year = start_year if month >= 9 else start_year + 1
        month_start = date(year, month, 1)
        month_end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
        months.append({"key": f"month_{month}", "label": MONTH_LABELS[month], "start": month_start, "end": month_end})

    return {
        "school_year": f"{start_year}-{start_year + 1}",
        "start_year": start_year,
        "period_start": period_start,
        "period_end": period_end,
        "months": months,
    }
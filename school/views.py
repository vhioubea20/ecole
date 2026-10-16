from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.utils import timezone

from .forms import SchoolClassForm, SchoolFeeForm, StudentForm, StudentPaymentForm, UserCreateForm, UserUpdateForm
from .exports import build_school_workbook
from .models import SchoolClass, SchoolFee, Student, StudentPayment
from .receipts import build_payment_receipt
from .services import fee_annual_amount, monthly_due_schedule, school_year_data

User = get_user_model()


def staff_required(view_func):
    return user_passes_test(lambda user: user.is_authenticated and user.is_staff)(view_func)


def school_permission_required(permission):
    def has_access(user):
        return user.is_authenticated and (user.is_staff or user.has_perm(f"school.{permission}"))

    return user_passes_test(has_access)


@login_required
def dashboard(request):
    context = {
        "student_count": Student.objects.filter(status=Student.Status.ACTIVE).count(),
        "class_count": SchoolClass.objects.count(),
        "user_count": User.objects.filter(is_active=True).count(),
        "recent_students": Student.objects.filter(status=Student.Status.ACTIVE)[:5],
    }
    return render(request, "school/dashboard.html", context)


@login_required
@staff_required
def export_all_excel(request):
    response = HttpResponse(
        build_school_workbook(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    filename = f"gestion_scolaire_{timezone.localdate():%Y%m%d}.xlsx"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@school_permission_required("view_student")
def student_list(request):
    students = Student.objects.all()
    search = request.GET.get("q", "").strip()
    if search:
        students = students.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(matricule__icontains=search)
            | Q(school_class__libelle__icontains=search)
            | Q(guardian_name__icontains=search)
        )
    status = request.GET.get("status", "")
    if status in Student.Status.values:
        students = students.filter(status=status)
    return render(request, "school/student_list.html", {"students": students, "search": search, "status": status})


@school_permission_required("view_student")
def student_badge(request, pk):
    student = get_object_or_404(Student.objects.select_related("school_class"), pk=pk)
    return render(request, "school/student_badge.html", {"student": student})


@school_permission_required("view_schoolclass")
def class_list(request):
    classes = SchoolClass.objects.annotate(student_count=Count("students"))
    return render(request, "school/class_list.html", {"classes": classes})


@school_permission_required("add_schoolclass")
def class_create(request):
    form = SchoolClassForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        school_class = form.save()
        messages.success(request, f"La classe « {school_class.libelle} » a été créée.")
        return redirect("class_list")
    return render(request, "school/class_form.html", {"form": form, "title": "Ajouter une classe"})


@school_permission_required("change_schoolclass")
def class_update(request, pk):
    school_class = get_object_or_404(SchoolClass, pk=pk)
    form = SchoolClassForm(request.POST or None, instance=school_class)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Le libellé de la classe a été modifié.")
        return redirect("class_list")
    return render(
        request,
        "school/class_form.html",
        {"form": form, "title": "Modifier une classe", "school_class": school_class},
    )


@school_permission_required("delete_schoolclass")
def class_delete(request, pk):
    school_class = get_object_or_404(SchoolClass, pk=pk)
    if request.method == "POST":
        if school_class.students.exists() or school_class.tuition_fees.exists():
            messages.error(request, "Cette classe ne peut pas être supprimée tant que des élèves ou des frais y sont rattachés.")
            return redirect("class_list")
        school_class.delete()
        messages.success(request, "La classe a été supprimée.")
        return redirect("class_list")
    return render(request, "school/confirm_delete.html", {"object": school_class, "cancel_url": "class_list"})


@school_permission_required("view_schoolfee")
def fee_list(request):
    fees = SchoolFee.objects.select_related("school_class")
    return render(request, "school/fee_list.html", {"fees": fees})


@school_permission_required("add_schoolfee")
def fee_create(request):
    form = SchoolFeeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Les frais de scolarité ont été enregistrés.")
        return redirect("fee_list")
    return render(request, "school/fee_form.html", {"form": form, "title": "Ajouter des frais de scolarité"})


@school_permission_required("change_schoolfee")
def fee_update(request, pk):
    fee = get_object_or_404(SchoolFee, pk=pk)
    form = SchoolFeeForm(request.POST or None, instance=fee)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Les frais de scolarité ont été modifiés.")
        return redirect("fee_list")
    return render(request, "school/fee_form.html", {"form": form, "title": "Modifier les frais", "fee": fee})


@school_permission_required("delete_schoolfee")
def fee_delete(request, pk):
    fee = get_object_or_404(SchoolFee, pk=pk)
    if request.method == "POST":
        fee.delete()
        messages.success(request, "Les frais de scolarité ont été supprimés.")
        return redirect("fee_list")
    return render(request, "school/confirm_delete.html", {"object": fee, "cancel_url": "fee_list"})


@school_permission_required("view_studentpayment")
def schooling_overview(request):
    year = school_year_data()
    money_field = DecimalField(max_digits=12, decimal_places=2)
    fee_by_class = {}
    for fee in SchoolFee.objects.filter(annee=year["school_year"]):
        fee_by_class.setdefault(fee.school_class_id, {})[fee.nature] = fee
    classes = SchoolClass.objects.annotate(
        student_count=Count("students", filter=Q(students__status=Student.Status.ACTIVE), distinct=True),
        total_paid=Coalesce(
            Sum(
                "students__payments__montant",
                filter=Q(
                    students__status=Student.Status.ACTIVE,
                    students__payments__date_paiement__gte=year["period_start"],
                    students__payments__date_paiement__lt=year["period_end"],
                ),
            ),
            Value(Decimal("0.00")),
            output_field=money_field,
        ),
    )
    rows = []
    for school_class in classes:
        class_fees = fee_by_class.get(school_class.pk, {})
        registration_fee = fee_annual_amount(class_fees.get(SchoolFee.Nature.REGISTRATION))
        tuition_fee = fee_annual_amount(class_fees.get(SchoolFee.Nature.TUITION))
        annual_fee = registration_fee + tuition_fee
        amount_due = annual_fee * school_class.student_count
        rows.append(
            {
                "school_class": school_class,
                "student_count": school_class.student_count,
                "registration_fee": registration_fee,
                "tuition_fee": tuition_fee,
                "tuition_mode": (
                    class_fees[SchoolFee.Nature.TUITION].get_mode_display()
                    if SchoolFee.Nature.TUITION in class_fees
                    else "—"
                ),
                "annual_fee": annual_fee,
                "amount_due": amount_due,
                "total_paid": school_class.total_paid,
                "balance": max(Decimal("0.00"), amount_due - school_class.total_paid),
            }
        )
    context = {
        **year,
        "class_rows": rows,
        "total_due": sum((row["amount_due"] for row in rows), Decimal("0.00")),
        "total_paid": sum((row["total_paid"] for row in rows), Decimal("0.00")),
    }
    context["total_balance"] = sum((row["balance"] for row in rows), Decimal("0.00"))
    return render(request, "school/schooling_overview.html", context)


@school_permission_required("view_studentpayment")
def schooling_class_detail(request, pk):
    year = school_year_data()
    school_class = get_object_or_404(SchoolClass, pk=pk)
    fee_records = {
        fee.nature: fee
        for fee in SchoolFee.objects.filter(school_class=school_class, annee=year["school_year"])
    }
    registration_fee = fee_annual_amount(fee_records.get(SchoolFee.Nature.REGISTRATION))
    tuition_fee_record = fee_records.get(SchoolFee.Nature.TUITION)
    tuition_fee = fee_annual_amount(tuition_fee_record)
    annual_fee = registration_fee + tuition_fee
    monthly_dues = monthly_due_schedule(registration_fee, tuition_fee_record)
    money_field = DecimalField(max_digits=12, decimal_places=2)
    annotations = {
        "total_paid": Coalesce(
            Sum(
                "payments__montant",
                filter=Q(
                    payments__date_paiement__gte=year["period_start"],
                    payments__date_paiement__lt=year["period_end"],
                ),
            ),
            Value(Decimal("0.00")),
            output_field=money_field,
        )
    }
    students = Student.objects.filter(school_class=school_class, status=Student.Status.ACTIVE).annotate(**annotations)
    rows = []
    for student in students:
        remaining_payment = student.total_paid
        monthly_payments = []
        for due in monthly_dues:
            paid = min(remaining_payment, due)
            remaining_payment -= paid
            if due > 0 and paid >= due:
                state = "paid"
            elif paid > 0:
                state = "partial"
            else:
                state = "unpaid"
            monthly_payments.append({"amount": paid, "state": state})
        rows.append(
            {
                "student": student,
                "monthly_payments": monthly_payments,
                "total_paid": student.total_paid,
                "amount_due": annual_fee,
                "balance": max(Decimal("0.00"), annual_fee - student.total_paid),
            }
        )
    return render(
        request,
        "school/schooling_class_detail.html",
        {
            **year,
            "school_class": school_class,
            "students": rows,
            "months": year["months"],
            "annual_fee": annual_fee,
            "registration_fee": registration_fee,
            "tuition_fee": tuition_fee,
            "tuition_mode": tuition_fee_record.get_mode_display() if tuition_fee_record else "—",
            "monthly_installment": monthly_dues[0] - registration_fee,
            "total_due": annual_fee * len(rows),
            "total_paid": sum((row["total_paid"] for row in rows), Decimal("0.00")),
            "can_add_payment": request.user.is_staff or request.user.has_perm("school.add_studentpayment"),
            "can_edit_student": request.user.is_staff or request.user.has_perm("school.change_student"),
        },
    )


@school_permission_required("view_studentpayment")
def student_payment_detail(request, pk):
    student = get_object_or_404(Student.objects.select_related("school_class"), pk=pk)
    year = school_year_data()
    payments = student.payments.all()
    total_paid = payments.filter(
        date_paiement__gte=year["period_start"],
        date_paiement__lt=year["period_end"],
    ).aggregate(total=Sum("montant"))["total"] or Decimal("0.00")
    class_fees = {
        fee.nature: fee
        for fee in SchoolFee.objects.filter(school_class=student.school_class, annee=year["school_year"])
    }
    amount_due = fee_annual_amount(class_fees.get(SchoolFee.Nature.REGISTRATION)) + fee_annual_amount(
        class_fees.get(SchoolFee.Nature.TUITION)
    )
    return render(
        request,
        "school/student_payment_detail.html",
        {
            **year,
            "student": student,
            "payments": payments,
            "total_paid": total_paid,
            "amount_due": amount_due,
            "balance": max(Decimal("0.00"), amount_due - total_paid),
            "can_add_payment": request.user.is_staff or request.user.has_perm("school.add_studentpayment"),
            "can_change_payment": request.user.is_staff or request.user.has_perm("school.change_studentpayment"),
            "can_delete_payment": request.user.is_staff or request.user.has_perm("school.delete_studentpayment"),
        },
    )


@school_permission_required("view_studentpayment")
def student_payment_receipt(request, pk):
    payment = get_object_or_404(
        StudentPayment.objects.select_related("student", "student__school_class"),
        pk=pk,
    )
    response = HttpResponse(
        build_payment_receipt(payment),
        content_type="application/pdf",
    )
    response["Content-Disposition"] = f'inline; filename="recu-paiement-{payment.pk:06d}.pdf"'
    return response


@school_permission_required("add_studentpayment")
def student_payment_create(request):
    initial = {}
    student_id = request.GET.get("student")
    if student_id:
        initial["student"] = get_object_or_404(Student, pk=student_id)
    form = StudentPaymentForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        payment = form.save()
        messages.success(request, "Le paiement a été enregistré.")
        return redirect("student_payment_detail", pk=payment.student_id)
    return render(request, "school/student_payment_form.html", {"form": form, "title": "Enregistrer un paiement"})


@school_permission_required("change_studentpayment")
def student_payment_update(request, pk):
    payment = get_object_or_404(StudentPayment, pk=pk)
    form = StudentPaymentForm(request.POST or None, instance=payment)
    if request.method == "POST" and form.is_valid():
        payment = form.save()
        messages.success(request, "Le paiement a été modifié.")
        return redirect("student_payment_detail", pk=payment.student_id)
    return render(
        request,
        "school/student_payment_form.html",
        {"form": form, "title": "Modifier un paiement", "payment": payment},
    )


@school_permission_required("delete_studentpayment")
def student_payment_delete(request, pk):
    payment = get_object_or_404(StudentPayment, pk=pk)
    if request.method == "POST":
        student_id = payment.student_id
        payment.delete()
        messages.success(request, "Le paiement a été supprimé.")
        return redirect("student_payment_detail", pk=student_id)
    return render(request, "school/student_payment_confirm_delete.html", {"payment": payment})


@school_permission_required("add_student")
def student_create(request):
    form = StudentForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        student = form.save()
        messages.success(request, f"Le dossier de {student} a été créé.")
        return redirect("student_list")
    return render(request, "school/student_form.html", {"form": form, "title": "Inscrire un élève"})


@school_permission_required("change_student")
def student_update(request, pk):
    student = get_object_or_404(Student, pk=pk)
    form = StudentForm(request.POST or None, request.FILES or None, instance=student)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Le dossier de l'élève a été mis à jour.")
        return redirect("student_list")
    return render(request, "school/student_form.html", {"form": form, "title": "Modifier le dossier", "student": student})


@school_permission_required("delete_student")
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == "POST":
        student.delete()
        messages.success(request, "Le dossier de l'élève a été supprimé.")
        return redirect("student_list")
    return render(request, "school/confirm_delete.html", {"object": student, "cancel_url": "student_list"})


@login_required
@staff_required
def user_list(request):
    users = User.objects.order_by("last_name", "first_name", "username")
    return render(request, "school/user_list.html", {"users": users})


@login_required
@staff_required
def user_create(request):
    form = UserCreateForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        messages.success(request, f"Le compte {user.username} a été créé.")
        return redirect("user_list")
    return render(request, "school/user_form.html", {"form": form, "title": "Créer un compte"})


@login_required
@staff_required
def user_update(request, pk):
    user = get_object_or_404(User, pk=pk, is_superuser=False)
    form = UserUpdateForm(request.POST or None, request.FILES or None, instance=user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Le compte {user.username} a été mis à jour.")
        return redirect("user_list")
    return render(request, "school/user_form.html", {"form": form, "title": "Modifier un compte", "target_user": user})


@login_required
@staff_required
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk, is_superuser=False)
    if request.method == "POST":
        if user.pk == request.user.pk:
            messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
            return redirect("user_list")
        user.delete()
        messages.success(request, "Le compte a été supprimé.")
        return redirect("user_list")
    return render(request, "school/confirm_delete.html", {"object": user, "cancel_url": "user_list"})


@require_POST
def logout_view(request):
    from django.contrib.auth import logout

    logout(request)
    return redirect("login")
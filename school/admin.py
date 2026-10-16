from django.contrib import admin

from .models import SchoolClass, SchoolFee, Student, StudentPayment


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ("libelle",)
    search_fields = ("libelle",)


@admin.register(SchoolFee)
class SchoolFeeAdmin(admin.ModelAdmin):
    list_display = (
        "school_class",
        "annee",
        "nature",
        "mode",
        "nombre_echeances",
        "tranche_standard_gne",
        "derniere_tranche_gne",
        "montant",
    )
    list_filter = ("annee", "school_class")

    @admin.display(description="Échéance standard (GNE)")
    def tranche_standard_gne(self, fee):
        return fee.montant_par_tranche

    @admin.display(description="Dernière échéance (GNE)")
    def derniere_tranche_gne(self, fee):
        return fee.montant_derniere_tranche


@admin.register(StudentPayment)
class StudentPaymentAdmin(admin.ModelAdmin):
    list_display = ("date_paiement", "student", "montant_gne")
    list_filter = ("date_paiement",)
    search_fields = ("student__matricule", "student__first_name", "student__last_name")

    @admin.display(description="Montant (GNE)")
    def montant_gne(self, payment):
        return payment.montant


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("matricule", "last_name", "first_name", "school_class", "guardian_name", "status")
    list_filter = ("status", "school_class")
    search_fields = ("matricule", "first_name", "last_name", "guardian_name")
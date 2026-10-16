from django.contrib import admin

from .models import SchoolClass, SchoolFee, Student, StudentPayment


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ("libelle",)
    search_fields = ("libelle",)


@admin.register(SchoolFee)
class SchoolFeeAdmin(admin.ModelAdmin):
    list_display = ("school_class", "annee", "nature", "montant")
    list_filter = ("annee", "school_class")


@admin.register(StudentPayment)
class StudentPaymentAdmin(admin.ModelAdmin):
    list_display = ("date_paiement", "student", "montant")
    list_filter = ("date_paiement",)
    search_fields = ("student__matricule", "student__first_name", "student__last_name")


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("matricule", "last_name", "first_name", "school_class", "guardian_name", "status")
    list_filter = ("status", "school_class")
    search_fields = ("matricule", "first_name", "last_name", "guardian_name")
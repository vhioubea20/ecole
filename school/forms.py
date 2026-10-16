from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Permission
from django.utils import timezone

from .models import SchoolClass, SchoolFee, Student, StudentPayment, UserProfile

User = get_user_model()


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            "first_name",
            "last_name",
            "date_of_birth",
            "school_class",
            "address",
            "photo",
            "guardian_name",
            "guardian_phone",
            "guardian_profession",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 3}),
            "photo": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }


class SchoolClassForm(forms.ModelForm):
    class Meta:
        model = SchoolClass
        fields = ["libelle"]
        labels = {"libelle": "Libellé"}


class SchoolFeeForm(forms.ModelForm):
    annee = forms.ChoiceField(label="Année scolaire")

    class Meta:
        model = SchoolFee
        fields = ["annee", "school_class", "nature", "montant"]
        labels = {
            "school_class": "Classe",
            "nature": "Nature",
            "montant": "Montant",
        }
        widgets = {
            "montant": forms.NumberInput(attrs={"min": "0.01", "step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.localdate()
        current_start = today.year if today.month >= 9 else today.year - 1
        years = [
            (f"{start}-{start + 1}", f"{start}-{start + 1}")
            for start in range(current_start - 3, current_start + 6)
        ]
        if self.instance.pk and self.instance.annee not in dict(years):
            years.insert(0, (self.instance.annee, self.instance.annee))
        self.fields["annee"].choices = years


class StudentChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, student):
        return f"{student.matricule} · {student.first_name} {student.last_name}"


class StudentPaymentForm(forms.ModelForm):
    student = StudentChoiceField(
        queryset=Student.objects.select_related("school_class").order_by("matricule"),
        label="Matricule élève",
    )

    class Meta:
        model = StudentPayment
        fields = ["date_paiement", "student", "montant"]
        labels = {"date_paiement": "Date", "montant": "Montant"}
        widgets = {
            "date_paiement": forms.DateInput(attrs={"type": "date"}),
            "montant": forms.NumberInput(attrs={"min": "0.01", "step": "0.01"}),
        }


class SchoolPermissionField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, permission):
        action, model_name = permission.codename.split("_", 1)
        actions = {
            "view": "Consulter",
            "add": "Ajouter",
            "change": "Modifier",
            "delete": "Supprimer",
        }
        models = {
            "student": "les élèves",
            "schoolclass": "les classes",
            "schoolfee": "les frais de scolarité",
            "studentpayment": "les paiements",
        }
        return f"{actions.get(action, action)} {models.get(model_name, model_name)}"


def school_permissions():
    return Permission.objects.filter(
        content_type__app_label="school",
        content_type__model__in=["student", "schoolclass", "schoolfee", "studentpayment"],
    ).order_by(
        "content_type__model", "codename"
    )


class UserCreateForm(UserCreationForm):
    email = forms.EmailField(label="Adresse courriel", required=False)
    first_name = forms.CharField(label="Prénom", max_length=150)
    last_name = forms.CharField(label="Nom", max_length=150)
    photo = forms.ImageField(label="Photo", required=False)
    role = forms.ChoiceField(
        label="Rôle",
        choices=(("admin", "Admin"), ("user", "Utilisateur")),
        help_text="Admin dispose de tous les droits. Les autorisations d'un utilisateur se règlent ci-dessous.",
    )
    permissions = SchoolPermissionField(
        queryset=Permission.objects.none(),
        required=False,
        label="Autorisations de l'utilisateur",
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")
        labels = {"username": "Identifiant"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["permissions"].queryset = school_permissions()
        self.fields["role"].initial = "user"

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        is_admin = self.cleaned_data["role"] == "admin"
        user.is_staff = is_admin
        user.is_superuser = False
        if commit:
            user.save()
            user.user_permissions.set(school_permissions() if is_admin else self.cleaned_data["permissions"])
            profile, _ = UserProfile.objects.get_or_create(user=user)
            if self.cleaned_data.get("photo"):
                profile.photo = self.cleaned_data["photo"]
                profile.save(update_fields=["photo"])
        return user


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(label="Adresse courriel", required=False)
    photo = forms.ImageField(label="Photo", required=False)
    role = forms.ChoiceField(
        label="Rôle",
        choices=(("admin", "Admin"), ("user", "Utilisateur")),
        help_text="Admin dispose de tous les droits. Les autorisations d'un utilisateur se règlent ci-dessous.",
    )
    permissions = SchoolPermissionField(
        queryset=Permission.objects.none(),
        required=False,
        label="Autorisations de l'utilisateur",
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "is_active")
        labels = {
            "username": "Identifiant",
            "first_name": "Prénom",
            "last_name": "Nom",
            "email": "Adresse courriel",
            "is_active": "Compte actif",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["permissions"].queryset = school_permissions()
        self.fields["role"].initial = "admin" if self.instance.is_staff else "user"
        if not self.instance.is_staff:
            self.fields["permissions"].initial = self.instance.user_permissions.filter(
                content_type__app_label="school"
            )

    def save(self, commit=True):
        user = super().save(commit=False)
        is_admin = self.cleaned_data["role"] == "admin"
        user.is_staff = is_admin
        user.is_superuser = False
        if commit:
            user.save()
            user.user_permissions.set(school_permissions() if is_admin else self.cleaned_data["permissions"])
            profile, _ = UserProfile.objects.get_or_create(user=user)
            if self.cleaned_data.get("photo"):
                profile.photo = self.cleaned_data["photo"]
                profile.save(update_fields=["photo"])
        return user
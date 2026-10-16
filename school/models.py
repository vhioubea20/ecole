import unicodedata

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone


class SchoolClass(models.Model):
    libelle = models.CharField("libellé", max_length=80, unique=True)

    class Meta:
        ordering = ["libelle"]
        verbose_name = "classe"
        verbose_name_plural = "classes"

    def __str__(self):
        return self.libelle


class SchoolFee(models.Model):
    class Nature(models.TextChoices):
        REGISTRATION = "inscription", "Inscription"
        TUITION = "scolarite", "Frais de scolarité"

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.PROTECT,
        related_name="tuition_fees",
        verbose_name="classe",
    )
    annee = models.CharField("année scolaire", max_length=9)
    nature = models.CharField("nature", max_length=16, choices=Nature.choices, default=Nature.TUITION)
    montant = models.DecimalField("montant", max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["-annee", "school_class__libelle"]
        verbose_name = "frais de scolarité"
        verbose_name_plural = "frais de scolarité"
        constraints = [
            models.UniqueConstraint(
                fields=["school_class", "annee", "nature"],
                name="unique_fee_per_class_year_nature",
            )
        ]

    def __str__(self):
        return f"{self.school_class.libelle} · {self.annee}"


class StudentPayment(models.Model):
    student = models.ForeignKey(
        "Student",
        on_delete=models.PROTECT,
        related_name="payments",
        verbose_name="élève",
    )
    date_paiement = models.DateField("date")
    montant = models.DecimalField("montant", max_digits=10, decimal_places=2)
    created_at = models.DateTimeField("créé le", auto_now_add=True)

    class Meta:
        ordering = ["-date_paiement", "-pk"]
        verbose_name = "paiement de scolarité"
        verbose_name_plural = "paiements de scolarité"

    def __str__(self):
        return f"{self.student.matricule} · {self.date_paiement:%d/%m/%Y} · {self.montant}"


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    photo = models.ImageField("photo", upload_to="users/", blank=True)

    def __str__(self):
        return f"Profil de {self.user.username}"


class Student(models.Model):
    class Gender(models.TextChoices):
        GIRL = "F", "Fille"
        BOY = "M", "Garçon"
        OTHER = "A", "Autre / non précisé"

    class Status(models.TextChoices):
        ACTIVE = "active", "Scolarisé(e)"
        LEFT = "left", "Parti(e)"

    matricule = models.CharField("matricule", max_length=24, unique=True, null=True, blank=True, editable=False)
    first_name = models.CharField("prénom", max_length=80)
    last_name = models.CharField("nom", max_length=80)
    date_of_birth = models.DateField("date de naissance", blank=True, null=True)
    gender = models.CharField("genre", max_length=1, choices=Gender.choices, default=Gender.OTHER)
    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.PROTECT,
        related_name="students",
        verbose_name="classe",
    )
    address = models.TextField("adresse", blank=True)
    photo = models.ImageField("photo", upload_to="students/", blank=True)
    guardian_name = models.CharField("personne responsable", max_length=160, blank=True)
    guardian_phone = models.CharField("numéro du responsable", max_length=30, blank=True)
    guardian_profession = models.CharField("profession du responsable", max_length=120, blank=True)
    enrollment_date = models.DateField("date d'inscription", default=timezone.localdate)
    status = models.CharField("statut", max_length=12, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField("créé le", auto_now_add=True)
    updated_at = models.DateTimeField("modifié le", auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]
        verbose_name = "élève"
        verbose_name_plural = "élèves"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            return super().save(*args, **kwargs)

        with transaction.atomic():
            super().save(*args, **kwargs)
            if self.matricule is None:
                first_names = [self._letters(part) for part in self.first_name.split()]
                first_names = [part for part in first_names if part]
                last_name = self._letters(self.last_name)
                first_code = first_names[0][:1] if len(first_names) > 1 else (first_names[0][:2] if first_names else "X")
                last_code = last_name[:2] or "X"
                self.matricule = f"{first_code}{last_code}{self.pk:04d}"
                super().save(update_fields=["matricule"])

    @staticmethod
    def _letters(value):
        normalized = unicodedata.normalize("NFKD", value)
        return "".join(char for char in normalized if char.isascii() and char.isalnum()).upper()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
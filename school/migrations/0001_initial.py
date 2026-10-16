import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Student",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("first_name", models.CharField(max_length=80, verbose_name="prénom")),
                ("last_name", models.CharField(max_length=80, verbose_name="nom")),
                ("date_of_birth", models.DateField(verbose_name="date de naissance")),
                (
                    "gender",
                    models.CharField(
                        choices=[("F", "Fille"), ("M", "Garçon"), ("A", "Autre / non précisé")],
                        default="A",
                        max_length=1,
                        verbose_name="genre",
                    ),
                ),
                ("class_name", models.CharField(max_length=80, verbose_name="classe")),
                ("guardian_name", models.CharField(max_length=160, verbose_name="responsable légal")),
                ("guardian_phone", models.CharField(max_length=30, verbose_name="téléphone du responsable")),
                ("guardian_email", models.EmailField(blank=True, max_length=254, verbose_name="courriel du responsable")),
                ("address", models.TextField(blank=True, verbose_name="adresse")),
                ("enrollment_date", models.DateField(default=django.utils.timezone.localdate, verbose_name="date d'inscription")),
                (
                    "status",
                    models.CharField(
                        choices=[("active", "Scolarisé(e)"), ("left", "Parti(e)")],
                        default="active",
                        max_length=12,
                        verbose_name="statut",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="créé le")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="modifié le")),
            ],
            options={
                "verbose_name": "élève",
                "verbose_name_plural": "élèves",
                "ordering": ["last_name", "first_name"],
            },
        ),
    ]
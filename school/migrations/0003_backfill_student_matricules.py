import unicodedata

from django.db import migrations


def fill_matricules(apps, schema_editor):
    Student = apps.get_model("school", "Student")
    database = schema_editor.connection.alias
    students = Student.objects.using(database).filter(matricule__isnull=True).iterator()

    for student in students:
        first_names = [
            _letters(part)
            for part in student.first_name.split()
        ]
        first_names = [part for part in first_names if part]
        first_code = first_names[0][:1] if len(first_names) > 1 else (first_names[0][:2] if first_names else "X")
        last_code = _letters(student.last_name)[:2] or "X"
        matricule = f"{first_code}{last_code}{student.pk:04d}"
        Student.objects.using(database).filter(pk=student.pk).update(matricule=matricule)


def _letters(value):
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if char.isascii() and char.isalnum()).upper()


class Migration(migrations.Migration):
    dependencies = [("school", "0002_remove_student_guardian_email_and_more")]

    operations = [migrations.RunPython(fill_matricules, migrations.RunPython.noop)]
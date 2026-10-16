from django.db import migrations, models
import django.db.models.deletion


def migrate_class_labels(apps, schema_editor):
    Student = apps.get_model("school", "Student")
    SchoolClass = apps.get_model("school", "SchoolClass")
    database = schema_editor.connection.alias

    for student in Student.objects.using(database).all().iterator():
        label = student.class_name.strip() or "Sans classe"
        school_class, _ = SchoolClass.objects.using(database).get_or_create(libelle=label)
        Student.objects.using(database).filter(pk=student.pk).update(school_class_id=school_class.pk)


class Migration(migrations.Migration):
    dependencies = [("school", "0003_backfill_student_matricules")]

    operations = [
        migrations.CreateModel(
            name="SchoolClass",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("libelle", models.CharField(max_length=80, unique=True, verbose_name="libellé")),
            ],
            options={
                "verbose_name": "classe",
                "verbose_name_plural": "classes",
                "ordering": ["libelle"],
            },
        ),
        migrations.AddField(
            model_name="student",
            name="school_class",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="students",
                to="school.schoolclass",
                verbose_name="classe",
            ),
        ),
        migrations.RunPython(migrate_class_labels, migrations.RunPython.noop),
        migrations.RemoveField(model_name="student", name="class_name"),
        migrations.AlterField(
            model_name="student",
            name="school_class",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="students",
                to="school.schoolclass",
                verbose_name="classe",
            ),
        ),
    ]
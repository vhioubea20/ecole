from django.conf import settings
from django.db import migrations


def create_existing_profiles(apps, schema_editor):
    UserProfile = apps.get_model("school", "UserProfile")
    app_label, model_name = settings.AUTH_USER_MODEL.split(".")
    User = apps.get_model(app_label, model_name)
    database = schema_editor.connection.alias
    existing_ids = UserProfile.objects.using(database).values_list("user_id", flat=True)
    profiles = [
        UserProfile(user_id=user_id)
        for user_id in User.objects.using(database).exclude(pk__in=existing_ids).values_list("pk", flat=True)
    ]
    UserProfile.objects.using(database).bulk_create(profiles, ignore_conflicts=True)


class Migration(migrations.Migration):
    dependencies = [
        ("school", "0006_userprofile"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [migrations.RunPython(create_existing_profiles, migrations.RunPython.noop)]
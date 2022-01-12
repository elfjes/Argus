# Generated by Django 3.2.6 on 2022-01-12 12:46

from django.db import migrations
import multiselectfield.db.fields


def copy_media_to_media_v1(apps, schema_editor):
    NotificationProfile = apps.get_model("argus_notificationprofile", "NotificationProfile")
    for notification_profile in NotificationProfile.objects.all():
        notification_profile.media_v1 = notification_profile.media
        notification_profile.save()


class Migration(migrations.Migration):

    dependencies = [
        ("argus_notificationprofile", "0003_alter_filter_filter"),
    ]

    operations = [
        migrations.AddField(
            model_name="notificationprofile",
            name="media_v1",
            field=multiselectfield.db.fields.MultiSelectField(
                choices=[("EM", "Email"), ("SM", "SMS")], default=["EM"], max_length=5
            ),
        ),
        migrations.RunPython(copy_media_to_media_v1),
    ]

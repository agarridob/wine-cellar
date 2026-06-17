from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wine", "0018_remove_django_celery_beat"),
    ]

    operations = [
        migrations.AddField(
            model_name="wine",
            name="external_bottle_image",
            field=models.URLField(blank=True, default=""),
        ),
    ]

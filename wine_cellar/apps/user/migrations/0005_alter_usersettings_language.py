from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0004_alter_usersettings_language"),
    ]

    operations = [
        migrations.AlterField(
            model_name="usersettings",
            name="language",
            field=models.CharField(
                choices=[
                    ("de-DE", "German"),
                    ("fr-FR", "French"),
                    ("en-gb", "British English"),
                    ("es-ES", "Spanish"),
                ],
                default="en-gb",
                max_length=7,
            ),
        ),
    ]

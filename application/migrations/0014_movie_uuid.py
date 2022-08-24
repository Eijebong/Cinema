# Generated by Django 4.1 on 2022-08-24 11:53

from django.db import migrations, models
import uuid

def populate_uuids(apps, _schema_editor):
    Movie = apps.get_model("application", "Movie")
    for movie in Movie.objects.all():
        movie.uuid = uuid.uuid4()
        movie.save()

class Migration(migrations.Migration):

    dependencies = [
        ("application", "0013_auto_20170626_1128"),
    ]

    operations = [
        migrations.AddField(
            model_name="movie",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, null=True),
        ),
        migrations.RunPython(populate_uuids, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name="movie",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, unique=True),
        ),
    ]

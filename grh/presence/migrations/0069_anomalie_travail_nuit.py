from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('presence', '0068_congevalide_notif_vue'),
    ]

    operations = [
        migrations.AddField(
            model_name='anomalie',
            name='travail_nuit',
            field=models.BooleanField(default=False),
        ),
    ]
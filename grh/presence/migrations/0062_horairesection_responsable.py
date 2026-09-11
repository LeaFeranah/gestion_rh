from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('presence', '0061_alter_anomalie_etat'),
    ]

    operations = [
        migrations.AddField(
            model_name='horairesection',
            name='responsable',
            field=models.CharField(
                blank=True,
                help_text="Nom du responsable de la section",
                max_length=150,
                null=True,
            ),
        ),
    ]
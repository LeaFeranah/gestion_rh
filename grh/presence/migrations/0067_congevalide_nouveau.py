from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Ajoute le champ « nouveau » pour la notification des congés à valider.
    Les congés DÉJÀ importés sont mis à False (pas de notification pour
    l'historique) ; seuls ceux qui arrivent ensuite d'Access seront « nouveaux ».
    """

    dependencies = [
        ('presence', '0066_alter_congevalide_duree'),
    ]

    operations = [
        # 1) Ajout avec False : toutes les lignes existantes = déjà vues
        migrations.AddField(
            model_name='congevalide',
            name='nouveau',
            field=models.BooleanField(default=False, db_index=True),
        ),
        # 2) Par défaut True pour les prochains congés créés par la synchro
        migrations.AlterField(
            model_name='congevalide',
            name='nouveau',
            field=models.BooleanField(default=True, db_index=True),
        ),
    ]
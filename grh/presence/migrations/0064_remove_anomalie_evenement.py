from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('presence', '0063_anomalie_evenement_alter_anomalie_etat'),
    ]

    # Le champ "evenement" n'existe plus dans 0063 : on ne le retire plus de
    # l'état Django (state_operations vide). Côté base, on supprime la colonne
    # seulement si elle existe encore (sans risque si elle a déjà été supprimée).
    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    "ALTER TABLE presence_anomalie DROP COLUMN IF EXISTS evenement_id;",
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[],
        ),
    ]
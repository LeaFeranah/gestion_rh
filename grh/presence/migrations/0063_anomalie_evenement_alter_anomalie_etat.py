from django.db import migrations, models


def _meme_heure(h1, h2):
    if h1 is None or h2 is None:
        return h1 is None and h2 is None
    return (h1.hour, h1.minute) == (h2.hour, h2.minute)


def recalculer_etats_ok(apps, schema_editor):
    """
    Corrige les anomalies marquées "OK" à tort :
    OK uniquement si heure par défaut == heure rectifiée (entrée ET sortie).
    Les marqueurs "présence supprimée" (OK + heures rectifiées vides) restent OK.
    """
    Anomalie = apps.get_model('presence', 'Anomalie')
    to_update = []
    for a in Anomalie.objects.filter(etat='ok').iterator(chunk_size=2000):
        rect_e, rect_s = a.heure_rectifiee_entree, a.heure_rectifiee_sortie
        if rect_e is None and rect_s is None:
            continue  # marqueur de suppression
        if _meme_heure(rect_e, a.heure_reelle_entree) and _meme_heure(rect_s, a.heure_reelle_sortie):
            continue  # vraiment OK

        if len(a.pointages_bruts_json or []) > 2:
            a.etat = 'multiples_pointages'
        elif rect_e is None:
            a.etat = 'pas_entree'
        elif rect_s is None or (a.heure_brute_entree and not a.heure_brute_sortie):
            a.etat = 'pas_sortie'
        else:
            a.etat = 'ecart_horaire'
        to_update.append(a)

        if len(to_update) >= 2000:
            Anomalie.objects.bulk_update(to_update, ['etat'])
            to_update = []

    if to_update:
        Anomalie.objects.bulk_update(to_update, ['etat'])


class Migration(migrations.Migration):

    dependencies = [
        ('presence', '0062_horairesection_responsable'),
    ]

    operations = [
        migrations.AlterField(
            model_name='anomalie',
            name='etat',
            field=models.CharField(
                choices=[
                    ('pas_entree', "Pas d'entrée"),
                    ('pas_sortie', 'Pas de sortie'),
                    ('multiples_pointages', 'Pointages multiples'),
                    ('retard_sortie', 'Retard de sortie'),
                    ('ecart_horaire', 'Écart horaire'),
                    ('ok', 'OK'),
                ],
                default='pas_entree',
                max_length=50,
            ),
        ),
        migrations.RunPython(recalculer_etats_ok, migrations.RunPython.noop),
    ]
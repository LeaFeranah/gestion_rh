"""
Congés validés  ->  événements de présence (table evenement).

Règle : quand un congé est coché « Validé » et que sa durée est >= 1 jour,
chaque jour de date_depart à date_retour passe en « CP ».
  ex. départ 15/10/2026, retour 16/10/2026, durée 2  ->  CP le 15 et le 16.
Le jour de retour n'est en CP que si l'heure de retour est >= 16h00 :
  ex. départ 19/10/2026, retour 20/10/2026 à 07h30  ->  CP le 19 seulement.

- Les jours déjà marqués par un autre motif saisi à la main (CM, RM, HP, ...)
  ne sont PAS écrasés ; seuls X / A / ANO (ou jour sans événement) passent en CP.
- Les événements créés ainsi portent un commentaire « Congé validé #<id> » :
  quand on décoche « Validé » (ou que le congé disparaît d'Access), seuls ces
  jours-là reviennent à « X ».
"""
import re
from datetime import time, timedelta
from decimal import Decimal, InvalidOperation

TYPE_CP = 'CP'
TYPES_REMPLACABLES = {'X', 'A', 'ANO', '', None}
DUREE_MIN = Decimal('1')


def marqueur(conge_id):
    return f"Congé validé #{conge_id}"


def _nb_jours_calendaires(conge):
    if conge.date_depart and conge.date_retour and conge.date_retour >= conge.date_depart:
        return (conge.date_retour - conge.date_depart).days + 1
    return None


def duree_en_jours(conge):
    """
    Durée du congé en JOURS (Decimal), ou None si la durée est en heures
    ou illisible.  Une durée en heures ne donne jamais de CP.

      "2", "2 j", "2 jours", "1,5"      -> jours
      "4h", "4 heures", "04:00", "3h30" -> heures  -> None
      nombre seul plus grand que le nombre de jours entre départ et retour
      (ex. "4" pour un départ et un retour le même jour)  -> heures -> None
    """
    texte = str(conge.duree or '').strip().lower()
    if not texte:
        return None

    # Unité explicite en heures (ou format horaire 04:00 / 1899-12-30 04:00:00)
    if ':' in texte or re.search(r'\d\s*h', texte) or 'heure' in texte or 'hr' in texte:
        return None

    m = re.search(r'\d+(?:[.,]\d+)?', texte)
    if not m:
        return None
    try:
        valeur = Decimal(m.group(0).replace(',', '.'))
    except InvalidOperation:
        return None

    if 'j' in texte:                 # "2 j", "2 jours" : unité explicite en jours
        return valeur

    # Nombre seul : ce sont des jours seulement s'il tient dans la période départ -> retour
    nb = _nb_jours_calendaires(conge)
    if nb is not None and valeur > nb:
        return None                  # ex. "4" sur une seule journée = 4 heures
    return valeur


def est_eligible_cp(conge):
    """True si le congé dure au moins 1 jour (en jours, pas en heures)."""
    d = duree_en_jours(conge)
    return d is not None and d >= DUREE_MIN


# Jour de retour : CP seulement si l'employé rentre à 16h00 ou plus tard.
#   retour 20/10 à 07h30  -> il travaille le 20  -> pas de CP le 20
#   retour 20/10 à 16h00  -> journée prise       -> CP le 20
HEURE_RETOUR_CP = time(16, 0)


def jours_du_conge(conge):
    """
    Liste des dates de date_depart à date_retour.
    Le jour de retour n'est compté que si heure_retour >= 16h00
    (ou si l'heure de retour n'est pas renseignée).
    """
    debut = conge.date_depart
    if not debut:
        return []
    fin = conge.date_retour
    if not fin:
        # Pas de date de retour : on se base sur la durée (2 jours -> départ + 1)
        d = duree_en_jours(conge) or DUREE_MIN
        fin = debut + timedelta(days=max(int(d.to_integral_value(rounding='ROUND_CEILING')) - 1, 0))
    elif fin > debut and conge.heure_retour and conge.heure_retour < HEURE_RETOUR_CP:
        fin = fin - timedelta(days=1)    # retour avant 16h : il travaille ce jour-là
    if fin < debut:
        return []
    return [debut + timedelta(days=i) for i in range((fin - debut).days + 1)]


def userid_du_conge(conge):
    from .models import UserInfo
    return (UserInfo.objects.filter(badgenumber=conge.matricule)
            .order_by('userid').values_list('userid', flat=True).first())


def appliquer_cp(conge):
    """Pose « CP » sur les jours du congé. Renvoie le nombre de jours marqués."""
    from .models import Evenement

    if not est_eligible_cp(conge):
        # Durée en heures ou < 1 jour : aucun CP (et on retire ceux posés à tort)
        retirer_cp(conge)
        return 0
    userid = userid_du_conge(conge)
    jours = jours_du_conge(conge)
    if userid is None or not jours:
        return 0

    # Si le congé a été modifié (dates déplacées), on nettoie d'abord ses anciens jours
    retirer_cp(conge, garder=set(jours), userid=userid)

    existants = {e.date: e for e in Evenement.objects.filter(userid=userid, date__in=jours)}
    note = marqueur(conge.id)
    a_creer, a_maj = [], []
    for j in jours:
        ev = existants.get(j)
        if ev is None:
            a_creer.append(Evenement(userid=userid, date=j, type_evenement=TYPE_CP, commentaire=note))
        elif ev.type_evenement in TYPES_REMPLACABLES:
            # (un CP déjà présent, manuel ou d'un autre congé, est laissé tel quel)
            ev.type_evenement, ev.commentaire = TYPE_CP, note
            a_maj.append(ev)
    if a_creer:
        Evenement.objects.bulk_create(a_creer, ignore_conflicts=True)
    for ev in a_maj:
        ev.save(update_fields=['type_evenement', 'commentaire', 'modifie_le'])
    return len(a_creer) + len(a_maj)


def retirer_cp(conge, garder=None, userid=None):
    """Remet à « X » les jours posés automatiquement par ce congé."""
    from .models import Evenement

    userid = userid if userid is not None else userid_du_conge(conge)
    if userid is None:
        return 0
    qs = Evenement.objects.filter(userid=userid, type_evenement=TYPE_CP,
                                  commentaire=marqueur(conge.id))
    if garder:
        qs = qs.exclude(date__in=garder)
    from django.utils import timezone
    return qs.update(type_evenement='X', commentaire='', modifie_le=timezone.now())


# ── Validation automatique par le motif ────────────────────────────────────
# Un motif saisi dans Access qui se termine par « OK » vaut validation :
#   "Congé annuel OK", "Maladie enfant ok", "Mariage OK." -> coché « Validé »
VALIDE_PAR_MOTIF = "Access (motif OK)"
_RE_MOTIF_OK = re.compile(r'(^|[^a-z0-9])ok[\s.!]*$', re.IGNORECASE)


def motif_ok(motif):
    return bool(motif and _RE_MOTIF_OK.search(motif.strip()))


def valider_par_motif(conge):
    """Coche « Validé » sur un congé dont le motif finit par OK, puis pose les CP."""
    from django.utils import timezone
    conge.valide = True
    conge.valide_par = VALIDE_PAR_MOTIF
    conge.valide_le = timezone.now()
    conge.nouveau = False
    conge.notif_vue = True
    conge.save(update_fields=['valide', 'valide_par', 'valide_le', 'nouveau', 'notif_vue'])
    return appliquer_cp(conge)


def valider_motifs_ok():
    """
    Coche « Validé » tous les congés dont le motif finit par « OK » et que
    personne n'a jamais décochés (valide_le vide). Renvoie le nombre cochés.
    Un congé décoché à la main garde une date dans valide_le : on n'y touche plus.
    """
    from django.db import transaction
    from .models import CongeValide
    candidats = [c for c in CongeValide.objects.filter(
                     valide=False, valide_le__isnull=True, motif__icontains='ok')
                 if motif_ok(c.motif)]
    with transaction.atomic():
        for c in candidats:
            valider_par_motif(c)
    return len(candidats)


def synchroniser_evenement(conge):
    """Applique ou retire les CP selon l'état « Validé » du congé."""
    return appliquer_cp(conge) if conge.valide else retirer_cp(conge)
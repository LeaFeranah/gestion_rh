"""
Utilitaires pour le calcul des présences
"""
from datetime import datetime, timedelta, time
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


def decimal_to_time(heure_decimal):
    """
    Convertit une heure décimale en objet time
    Ex: 7.50 -> time(7, 30), 17.83 -> time(17, 50)
    Format: heures.centièmes (1 centième = 0.6 minutes)
    """
    if heure_decimal is None:
        return None
    try:
        heure_decimal = float(heure_decimal)
        heures = int(heure_decimal)
        centiemes = heure_decimal - heures
        minutes_fraction = centiemes * 100 * 0.6
        minutes = int(round(minutes_fraction))
        if minutes >= 60:
            heures += 1
            minutes = 0
        heures = heures % 24
        return time(heures, minutes)
    except (ValueError, TypeError, AttributeError) as e:
        logger.error(f"Erreur dans decimal_to_time: {heure_decimal}, erreur: {e}")
        return None


def time_to_decimal(time_obj):
    """
    Convertit un objet time en décimal (format heures.centièmes)
    """
    if time_obj is None:
        return None
    try:
        heures = time_obj.hour
        minutes = time_obj.minute
        centiemes = (minutes * 100) / 60
        decimal_value = heures + (centiemes / 100)
        return Decimal(str(round(decimal_value, 2)))
    except Exception as e:
        logger.error(f"Erreur dans time_to_decimal: {time_obj}, erreur: {e}")
        return None


def calculer_retard_entree(heure_reelle, heure_prevue, tolerance_minutes=20):
    if heure_reelle is None or heure_prevue is None:
        return 0, heure_reelle
    try:
        today = datetime.today().date()
        dt_reelle = datetime.combine(today, heure_reelle)
        dt_prevue = datetime.combine(today, heure_prevue)
        diff = dt_reelle - dt_prevue
        diff_minutes = diff.total_seconds() / 60
        if diff_minutes <= tolerance_minutes:
            return 0, heure_prevue
        retard_minutes = diff_minutes - tolerance_minutes
        return int(retard_minutes), heure_reelle
    except Exception as e:
        logger.error(f"Erreur dans calculer_retard_entree: {e}")
        return 0, heure_reelle


def calculer_sortie_anticipee(heure_reelle, heure_prevue, tolerance_minutes=5):
    if heure_reelle is None or heure_prevue is None:
        return 0, heure_reelle
    try:
        today = datetime.today().date()
        dt_reelle = datetime.combine(today, heure_reelle)
        dt_prevue = datetime.combine(today, heure_prevue)
        diff = dt_prevue - dt_reelle
        diff_minutes = diff.total_seconds() / 60
        if diff_minutes <= tolerance_minutes:
            return 0, heure_prevue
        if diff_minutes > tolerance_minutes:
            sortie_anticipee = int(diff_minutes - tolerance_minutes)
            return sortie_anticipee, heure_reelle
        return 0, heure_prevue
    except Exception as e:
        logger.error(f"Erreur dans calculer_sortie_anticipee: {e}")
        return 0, heure_reelle


def calculer_heures_travaillees(heure_entree, heure_sortie, pause_minutes=60):
    if heure_entree is None or heure_sortie is None:
        return Decimal('0')
    try:
        today = datetime.today().date()
        dt_entree = datetime.combine(today, heure_entree)
        dt_sortie = datetime.combine(today, heure_sortie)
        if dt_sortie <= dt_entree:
            return Decimal('0')
        diff = dt_sortie - dt_entree
        minutes_totales = diff.total_seconds() / 60
        minutes_travaillees = minutes_totales - pause_minutes
        if minutes_travaillees < 0:
            return Decimal('0')
        heures = minutes_travaillees / 60
        return Decimal(str(round(heures, 2)))
    except Exception as e:
        logger.error(f"Erreur dans calculer_heures_travaillees: {e}")
        return Decimal('0')


def analyser_presence(heure_entree_reelle, heure_sortie_reelle, heure_entree_prevue,
                      heure_sortie_prevue, date_pointage):
    try:
        retard_minutes, heure_entree_comptabilisee = calculer_retard_entree(
            heure_entree_reelle, heure_entree_prevue)
        sortie_anticipee_minutes, heure_sortie_comptabilisee = calculer_sortie_anticipee(
            heure_sortie_reelle, heure_sortie_prevue)
        heures_travaillees = calculer_heures_travaillees(
            heure_entree_comptabilisee, heure_sortie_comptabilisee)
        heures_prevues = calculer_heures_travaillees(heure_entree_prevue, heure_sortie_prevue)
        return {
            'heure_entree_reelle': heure_entree_reelle,
            'heure_sortie_reelle': heure_sortie_reelle,
            'heure_entree_prevue': heure_entree_prevue,
            'heure_sortie_prevue': heure_sortie_prevue,
            'heure_entree_comptabilisee': heure_entree_comptabilisee,
            'heure_sortie_comptabilisee': heure_sortie_comptabilisee,
            'retard_minutes': retard_minutes,
            'sortie_anticipee_minutes': sortie_anticipee_minutes,
            'heures_travaillees': float(heures_travaillees),
            'heures_prevues': float(heures_prevues),
            'est_en_retard': retard_minutes > 0,
            'est_sorti_en_avance': sortie_anticipee_minutes > 0,
            'difference_heures': float(heures_travaillees - heures_prevues),
        }
    except Exception as e:
        logger.error(f"Erreur dans analyser_presence: {e}")
        return {
            'heure_entree_reelle': heure_entree_reelle,
            'heure_sortie_reelle': heure_sortie_reelle,
            'heure_entree_prevue': heure_entree_prevue,
            'heure_sortie_prevue': heure_sortie_prevue,
            'heure_entree_comptabilisee': None,
            'heure_sortie_comptabilisee': None,
            'retard_minutes': 0,
            'sortie_anticipee_minutes': 0,
            'heures_travaillees': 0.0,
            'heures_prevues': 0.0,
            'est_en_retard': False,
            'est_sorti_en_avance': False,
            'difference_heures': 0.0,
        }


# def get_section_employe(badgenumber):
#     try:
#         from personnel.models import InformationPersonnelle
#         employe = InformationPersonnelle.objects.select_related(
#             'information_professionnelle'
#         ).get(numero_matricule=badgenumber)
#         if hasattr(employe, 'information_professionnelle'):
#             return employe.information_professionnelle.section
#         return 'ADMINISTRATION'
#     except Exception as e:
#         logger.warning(f"Section non trouvée pour {badgenumber}: {e}")
#         return 'ADMINISTRATION'


# presence/utils.py — remplacer get_section_employe

def get_section_employe(badgenumber: str) -> str:
    """
    Recherche rapide via UserSection (db_user_section).
    Fallback sur InformationPersonnelle si la table n'est pas encore peuplée.
    """
    try:
        from presence.models import UserSection, UserInfo
        user = UserInfo.objects.get(badgenumber=badgenumber)
        us   = UserSection.objects.select_related('section').get(user=user)
        return us.section.nom_section if us.section else 'ADMINISTRATION'
    except Exception:
        pass
    # Fallback legacy
    try:
        from personnel.models import InformationPersonnelle
        emp = InformationPersonnelle.objects.select_related(
            'information_professionnelle'
        ).get(numero_matricule=badgenumber)
        if hasattr(emp, 'information_professionnelle'):
            ip  = emp.information_professionnelle
            raw = ip.responsable_section.strip() if ip.responsable_section else ""
            return raw.upper() if raw else (ip.section.strip().upper() if ip.section else 'ADMINISTRATION')
    except Exception as e:
        logger.warning(f"Section non trouvée pour {badgenumber}: {e}")
    return 'ADMINISTRATION'


def build_user_section_map() -> dict:
    """
    Retourne {userid: nom_section} en UNE seule requête SQL.
    """
    from presence.models import UserSection
    return {
        us.userid: us.section.nom_section
        for us in UserSection.objects.select_related('section').all()
        if us.section_id is not None
    }

def format_duree(minutes):
    if minutes is None or minutes == 0:
        return "0h"
    heures = int(minutes // 60)
    mins = int(minutes % 60)
    if heures > 0 and mins > 0:
        return f"{heures}h {mins}min"
    elif heures > 0:
        return f"{heures}h"
    else:
        return f"{mins}min"


def calculer_heures_supplementaires(heures_travaillees, heures_contractuelles):
    try:
        if heures_travaillees > heures_contractuelles:
            return heures_travaillees - heures_contractuelles
        return Decimal('0')
    except Exception:
        return Decimal('0')


def est_jour_ferie(date_pointage):
    return False


# def analyser_pointages_jour(pointages_bruts, heure_entree_prevue, heure_sortie_prevue,
#                              seuil_minutes=30):
#     if not pointages_bruts:
#         return None, None, None, []

#     tries = sorted(pointages_bruts, key=lambda p: p.checktime)

#     liste_bruts = [
#         {'time': p.checktime.time().strftime('%H:%M'), 'checktype': p.checktype.upper()}
#         for p in tries
#     ]

#     entrees = [p for p in tries if p.checktype.upper() == 'O']
#     sorties  = [p for p in tries if p.checktype.upper() == 'I']

#     # ── Cas 1 : un seul pointage ──────────────────────────────────────────────
#     if len(tries) == 1:
#         if sorties and not entrees:
#             # Seulement I → pas d'entrée
#             return None, sorties[0].checktime.time(), 'pas_entree', liste_bruts
#         else:
#             # Seulement O → pas de sortie
#             return entrees[0].checktime.time(), None, 'pas_sortie', liste_bruts

#     premier = tries[0]
#     dernier  = tries[-1]
#     ecart_minutes = (dernier.checktime - premier.checktime).total_seconds() / 60.0

#     # ── Cas 2 : écart insuffisant ─────────────────────────────────────────────
#     if ecart_minutes < seuil_minutes:
#         if sorties and not entrees:
#             # Tous I trop proches → pas d'entrée
#             return None, sorties[0].checktime.time(), 'pas_entree', liste_bruts
#         # Tous O ou mixte trop proches → pas de sortie
#         return premier.checktime.time(), None, 'pas_sortie', liste_bruts

#     # ── Cas 3 : plus de 2 pointages avec écart suffisant ─────────────────────
#     if len(tries) > 2:
#         return premier.checktime.time(), dernier.checktime.time(), 'multiples_pointages', liste_bruts

#     # ── Cas 4 : exactement 2 pointages, écart >= 30 min ──────────────────────
#     # Peu importe le type (I+I, O+O, O+I, I+O)
#     # L'employé ne sait pas pointer → premier=entrée, dernier=sortie
#     heure_entree_brute = premier.checktime.time()
#     heure_sortie_brute = dernier.checktime.time()

#     heure_entree_corrigee = heure_entree_prevue if (heure_entree_prevue and heure_entree_brute <= heure_entree_prevue) else heure_entree_brute
#     heure_sortie_corrigee = heure_sortie_prevue if (heure_sortie_prevue and heure_sortie_brute >= heure_sortie_prevue) else heure_sortie_brute

#     return heure_entree_corrigee, heure_sortie_corrigee, None, liste_bruts



# def analyser_pointages_jour(pointages_bruts, heure_entree_prevue, heure_sortie_prevue,
#                              seuil_minutes=30):
#     if not pointages_bruts:
#         return None, None, None, []

#     tries = sorted(pointages_bruts, key=lambda p: p.checktime)

#     liste_bruts_complet = [
#         {'time': p.checktime.time().strftime('%H:%M'), 'checktype': p.checktype.upper()}
#         for p in tries
#     ]

#     entrees = [p for p in tries if p.checktype.upper() == 'O']
#     sorties  = [p for p in tries if p.checktype.upper() == 'I']

#     # ── Cas 1 : un seul pointage ──────────────────────────────────────────
#     if len(tries) == 1:
#         if sorties and not entrees:
#             return None, sorties[0].checktime.time(), 'pas_entree', liste_bruts_complet
#         else:
#             return entrees[0].checktime.time(), None, 'pas_sortie', liste_bruts_complet

#     premier = tries[0]
#     dernier  = tries[-1]
#     ecart_minutes = (dernier.checktime - premier.checktime).total_seconds() / 60.0

#     # ── Cas 2 : écart total insuffisant (< 30 min) → doublon ─────────────
#     if ecart_minutes < seuil_minutes:
#         if sorties and not entrees:
#             return None, sorties[0].checktime.time(), 'pas_entree', liste_bruts_complet
#         return premier.checktime.time(), None, 'pas_sortie', liste_bruts_complet

#     # ── Cas 3 : plus de 2 pointages avec écart total >= 30 min ───────────
#     if len(tries) > 2:
#         # Garder uniquement les pointages espacés d'au moins 15 minutes du précédent
#         filtres = [tries[0]]
#         for p in tries[1:]:
#             ecart = (p.checktime - filtres[-1].checktime).total_seconds() / 60.0
#             if ecart >= 15:
#                 filtres.append(p)

#         liste_bruts_filtres = [
#             {'time': p.checktime.time().strftime('%H:%M'), 'checktype': p.checktype.upper()}
#             for p in filtres
#         ]

#         # Après filtrage : 1 seul pointage restant
#         if len(filtres) == 1:
#             if filtres[0].checktype.upper() == 'I':
#                 return None, filtres[0].checktime.time(), 'pas_entree', liste_bruts_filtres
#             return filtres[0].checktime.time(), None, 'pas_sortie', liste_bruts_filtres

#         # Après filtrage : exactement 2 pointages → cas normal (entrée + sortie)
#         if len(filtres) == 2:
#             heure_entree_brute = filtres[0].checktime.time()
#             heure_sortie_brute = filtres[-1].checktime.time()
#             heure_entree_corrigee = heure_entree_prevue if (heure_entree_prevue and heure_entree_brute <= heure_entree_prevue) else heure_entree_brute
#             heure_sortie_corrigee = heure_sortie_prevue if (heure_sortie_prevue and heure_sortie_brute >= heure_sortie_prevue) else heure_sortie_brute
#             return heure_entree_corrigee, heure_sortie_corrigee, None, liste_bruts_filtres

#         # Après filtrage : encore 3+ pointages distincts → multiples_pointages
#         # avec uniquement les pointages filtrés (espacés >= 15 min) affichés
#         return filtres[0].checktime.time(), filtres[-1].checktime.time(), 'multiples_pointages', liste_bruts_filtres

#     # ── Cas 4 : exactement 2 pointages, écart >= 30 min → cas normal ─────
#     heure_entree_brute = premier.checktime.time()
#     heure_sortie_brute = dernier.checktime.time()
#     heure_entree_corrigee = heure_entree_prevue if (heure_entree_prevue and heure_entree_brute <= heure_entree_prevue) else heure_entree_brute
#     heure_sortie_corrigee = heure_sortie_prevue if (heure_sortie_prevue and heure_sortie_brute >= heure_sortie_prevue) else heure_sortie_brute
#     return heure_entree_corrigee, heure_sortie_corrigee, None, liste_bruts_complet

def analyser_pointages_jour(pointages_bruts, heure_entree_prevue, heure_sortie_prevue,
                             seuil_minutes=30):
    if not pointages_bruts:
        return None, None, None, []

    tries = sorted(pointages_bruts, key=lambda p: p.checktime)

    liste_bruts_complet = [
        {'time': p.checktime.time().strftime('%H:%M'), 'checktype': p.checktype.upper()}
        for p in tries
    ]

    entrees = [p for p in tries if p.checktype.upper() == 'O']
    sorties  = [p for p in tries if p.checktype.upper() == 'I']

    # ── Cas 1 : un seul pointage ──────────────────────────────────────────
    if len(tries) == 1:
        if sorties and not entrees:
            return None, sorties[0].checktime.time(), 'pas_entree', liste_bruts_complet
        elif entrees:
            return entrees[0].checktime.time(), None, 'pas_sortie', liste_bruts_complet
        else:
            # checktype inconnu (ni 'O' ni 'I') — traité comme une entrée
            return tries[0].checktime.time(), None, 'pas_sortie', liste_bruts_complet

    premier = tries[0]
    dernier  = tries[-1]
    ecart_minutes = (dernier.checktime - premier.checktime).total_seconds() / 60.0

    # ── Cas 2 : écart total insuffisant (< 30 min) → doublon ─────────────
    if ecart_minutes < seuil_minutes:
        if sorties and not entrees:
            return None, sorties[0].checktime.time(), 'pas_entree', liste_bruts_complet
        return premier.checktime.time(), None, 'pas_sortie', liste_bruts_complet

    # ── Cas 3 : plus de 2 pointages avec écart total >= 30 min ───────────
    if len(tries) > 2:
        # Garder uniquement les pointages espacés d'au moins 15 minutes du précédent
        filtres = [tries[0]]
        for p in tries[1:]:
            ecart = (p.checktime - filtres[-1].checktime).total_seconds() / 60.0
            if ecart >= 15:
                filtres.append(p)

        liste_bruts_filtres = [
            {'time': p.checktime.time().strftime('%H:%M'), 'checktype': p.checktype.upper()}
            for p in filtres
        ]

        entrees_filtres = [p for p in filtres if p.checktype.upper() == 'O']
        sorties_filtres  = [p for p in filtres if p.checktype.upper() == 'I']

        # Après filtrage : 1 seul pointage restant
        if len(filtres) == 1:
            if filtres[0].checktype.upper() == 'I':
                return None, filtres[0].checktime.time(), 'pas_entree', liste_bruts_filtres
            elif filtres[0].checktype.upper() == 'O':
                return filtres[0].checktime.time(), None, 'pas_sortie', liste_bruts_filtres
            else:
                # checktype inconnu
                return filtres[0].checktime.time(), None, 'pas_sortie', liste_bruts_filtres

        # Après filtrage : exactement 2 pointages → cas normal (entrée + sortie)
        if len(filtres) == 2:
            heure_entree_brute = filtres[0].checktime.time()
            heure_sortie_brute = filtres[-1].checktime.time()
            heure_entree_corrigee = heure_entree_prevue if (heure_entree_prevue and heure_entree_brute <= heure_entree_prevue) else heure_entree_brute
            heure_sortie_corrigee = heure_sortie_prevue if (heure_sortie_prevue and heure_sortie_brute >= heure_sortie_prevue) else heure_sortie_brute
            return heure_entree_corrigee, heure_sortie_corrigee, None, liste_bruts_filtres

        # Après filtrage : encore 3+ pointages distincts → multiples_pointages
        return filtres[0].checktime.time(), filtres[-1].checktime.time(), 'multiples_pointages', liste_bruts_filtres

    # ── Cas 4 : exactement 2 pointages, écart >= 30 min → cas normal ─────
    heure_entree_brute = premier.checktime.time()
    heure_sortie_brute = dernier.checktime.time()
    heure_entree_corrigee = heure_entree_prevue if (heure_entree_prevue and heure_entree_brute <= heure_entree_prevue) else heure_entree_brute
    heure_sortie_corrigee = heure_sortie_prevue if (heure_sortie_prevue and heure_sortie_brute >= heure_sortie_prevue) else heure_sortie_brute
    return heure_entree_corrigee, heure_sortie_corrigee, None, liste_bruts_complet


def corriger_pointages_automatique(pointages_bruts, heure_entree_prevue, heure_sortie_prevue,
                                    seuil_minutes=30):
    """Rétro-compatibilité — délègue à analyser_pointages_jour."""
    if not pointages_bruts:
        return None, None, False
    entree, sortie, type_anomalie, _ = analyser_pointages_jour(
        pointages_bruts, heure_entree_prevue, heure_sortie_prevue, seuil_minutes
    )
    return entree, sortie, (type_anomalie is not None)
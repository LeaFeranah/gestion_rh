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



# ── Constantes RESPONSABLE ──────────────────────────────────────────────────
RESPONSABLE_VARIANTS = {
    'RESPONSABLE', 'RESPONSABLE 0', 'RESPONSABLE 1',
    'RESPONSABLE 2', 'RESPONSABLE 3', 'RESPONSABLE RAPHIA'
}

def _effective_section(ip_section: str, ip_responsable_section: str) -> str:
    """Retourne la section effective : responsable_section pour les RESPONSABLE."""
    section_upper = (ip_section or '').strip().upper()
    if section_upper in RESPONSABLE_VARIANTS or section_upper.startswith('RESPONSABLE '):
        return (ip_responsable_section or '').strip() or ip_section or 'ADMINISTRATION'
    return (ip_section or 'ADMINISTRATION').strip()


def get_section_employe(badgenumber: str) -> str:
    try:
        from presence.models import UserSection, UserInfo
        user = UserInfo.objects.get(badgenumber=badgenumber)
        us = UserSection.objects.select_related('section').get(user=user)
        if us.section:
            # On vérifie si c'est un RESPONSABLE via InformationProfessionnelle
            try:
                from personnel.models import InformationPersonnelle
                emp = InformationPersonnelle.objects.select_related(
                    'information_professionnelle'
                ).get(numero_matricule=badgenumber)
                if hasattr(emp, 'information_professionnelle'):
                    ip = emp.information_professionnelle
                    return _effective_section(ip.section, ip.responsable_section)
            except Exception:
                pass
            return us.section.nom_section
    except Exception:
        pass

    # Fallback InformationProfessionnelle
    try:
        from personnel.models import InformationPersonnelle
        emp = InformationPersonnelle.objects.select_related(
            'information_professionnelle'
        ).get(numero_matricule=badgenumber)
        if hasattr(emp, 'information_professionnelle'):
            ip = emp.information_professionnelle
            return _effective_section(ip.section, ip.responsable_section)
    except Exception as e:
        logger.warning(f"Section non trouvée pour {badgenumber}: {e}")
    return 'ADMINISTRATION'


_user_section_cache = {'data': None, 'ts': 0}

def build_user_section_map(max_age_seconds=300) -> dict:
    """
    Retourne {userid: section_effective} avec cache 5 minutes.
    """
    import time
    now = time.time()
    if _user_section_cache['data'] is not None and \
       (now - _user_section_cache['ts']) < max_age_seconds:
        return _user_section_cache['data']

    from presence.models import UserInfo
    from personnel.models import InformationPersonnelle, InformationProfessionnelle

    active_badges = set(get_active_badgenumbers())

    userid_to_badge = {
        u.userid: u.badgenumber
        for u in UserInfo.objects.filter(badgenumber__in=active_badges)
    }
    active_userids = set(userid_to_badge.keys())

    badge_to_section = {}
    for ip in (
        InformationProfessionnelle.objects
        .select_related('employe')
        .filter(employe__numero_matricule__in=active_badges)
    ):
        badge = ip.employe.numero_matricule
        badge_to_section[badge] = _effective_section(ip.section, ip.responsable_section)

    result = {}
    for userid, badge in userid_to_badge.items():
        if badge in badge_to_section and badge_to_section[badge]:
            result[userid] = badge_to_section[badge]

    from presence.models import UserSection
    for us in (
        UserSection.objects
        .select_related('section')
        .filter(userid__in=active_userids)
    ):
        if us.userid not in result and us.section_id is not None:
            result[us.userid] = us.section.nom_section

    # Mettre en cache
    _user_section_cache['data'] = result
    _user_section_cache['ts'] = now
    return result


def invalidate_user_section_cache():
    """Appeler si un employé change de section."""
    _user_section_cache['data'] = None
    _user_section_cache['ts'] = 0

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

# ↓ AJOUTER ICI (avant analyser_pointages_jour)
# def _choisir_heure_sortie(heure_brute, heure_prevue, seuil_retard_minutes=15):
#     if not heure_prevue or not heure_brute:
#         return heure_brute, False
#     from datetime import datetime
#     ref = datetime.today().date()
#     dt_brute  = datetime.combine(ref, heure_brute)
#     dt_prevue = datetime.combine(ref, heure_prevue)
#     diff_minutes = (dt_brute - dt_prevue).total_seconds() / 60
#     if diff_minutes >= seuil_retard_minutes:
#         return heure_prevue, True
#     elif diff_minutes >= 0:
#         return heure_prevue, False
#     else:
#         return heure_brute.replace(second=0, microsecond=0), False
def _choisir_heure_sortie(heure_brute, heure_prevue, seuil_retard_minutes=15, tolerance_avance_minutes=5):
    if not heure_prevue or not heure_brute:
        return heure_brute, False
    from datetime import datetime
    ref = datetime.today().date()
    dt_brute  = datetime.combine(ref, heure_brute)
    dt_prevue = datetime.combine(ref, heure_prevue)
    diff_minutes = (dt_brute - dt_prevue).total_seconds() / 60
    if diff_minutes >= seuil_retard_minutes:
        return heure_prevue, True
    elif diff_minutes >= -tolerance_avance_minutes:
        # sortie dans la fenêtre [prevue-5min, prevue+15min[ → on arrondit à l'heure prévue
        return heure_prevue, False
    else:
        return heure_brute, False


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
#         elif entrees:
#             return entrees[0].checktime.time(), None, 'pas_sortie', liste_bruts_complet
#         else:
#             return tries[0].checktime.time(), None, 'pas_sortie', liste_bruts_complet

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
#         filtres = [tries[0]]
#         for p in tries[1:]:
#             ecart = (p.checktime - filtres[-1].checktime).total_seconds() / 60.0
#             if ecart >= 15:
#                 filtres.append(p)

#         liste_bruts_filtres = [
#             {'time': p.checktime.time().strftime('%H:%M'), 'checktype': p.checktype.upper()}
#             for p in filtres
#         ]

#         if len(filtres) == 1:
#             if filtres[0].checktype.upper() == 'I':
#                 return None, filtres[0].checktime.time(), 'pas_entree', liste_bruts_filtres
#             else:
#                 return filtres[0].checktime.time(), None, 'pas_sortie', liste_bruts_filtres

#         if len(filtres) == 2:
#             heure_entree_brute = filtres[0].checktime.time()
#             heure_sortie_brute = filtres[-1].checktime.time()
#             heure_entree_corrigee = (
#                 heure_entree_prevue
#                 if (heure_entree_prevue and heure_entree_brute <= heure_entree_prevue)
#                 else heure_entree_brute
#             )
#             heure_sortie_corrigee, retard_sortie = _choisir_heure_sortie(
#                 heure_sortie_brute, heure_sortie_prevue
#             )
#             if retard_sortie:
#                 return heure_entree_corrigee, heure_sortie_corrigee, 'retard_sortie', liste_bruts_filtres
#             return heure_entree_corrigee, heure_sortie_corrigee, None, liste_bruts_filtres

#         return filtres[0].checktime.time(), filtres[-1].checktime.time(), 'multiples_pointages', liste_bruts_filtres

#     # ── Cas 4 : exactement 2 pointages, écart >= 30 min ──────────────────
#     heure_entree_brute = premier.checktime.time()
#     heure_sortie_brute = dernier.checktime.time()
#     heure_entree_corrigee = (
#         heure_entree_prevue
#         if (heure_entree_prevue and heure_entree_brute <= heure_entree_prevue)
#         else heure_entree_brute
#     )
#     heure_sortie_corrigee, retard_sortie = _choisir_heure_sortie(
#         heure_sortie_brute, heure_sortie_prevue
#     )
#     if retard_sortie:
#         return heure_entree_corrigee, heure_sortie_corrigee, 'retard_sortie', liste_bruts_complet
#     return heure_entree_corrigee, heure_sortie_corrigee, None, liste_bruts_complet

# def analyser_pointages_jour(pointages_bruts, heure_entree_prevue, heure_sortie_prevue,
#                              seuil_minutes=30):
#     """
#     Analyse les pointages d'un employé pour un jour donné
#     Retourne: (heure_entree, heure_sortie, type_anomalie, liste_bruts)
    
#     type_anomalie peut être:
#     - None: OK
#     - 'pas_entree'
#     - 'pas_sortie' 
#     - 'multiples_pointages'
#     - 'retard_sortie'
#     - 'entree_trop_tot'  # ← NOUVEAU
#     """
#     if not pointages_bruts:
#         return None, None, None, []

#     tries = sorted(pointages_bruts, key=lambda p: p.checktime)

#     liste_bruts_complet = [
#         {'time': p.checktime.time().strftime('%H:%M'), 'checktype': p.checktype.upper()}
#         for p in tries
#     ]

#     entrees = [p for p in tries if p.checktype.upper() == 'O']
#     sorties = [p for p in tries if p.checktype.upper() == 'I']

#     # ── Cas 1 : un seul pointage ──────────────────────────────────────────
#     if len(tries) == 1:
#         if sorties and not entrees:
#             return None, sorties[0].checktime.time(), 'pas_entree', liste_bruts_complet
#         elif entrees:
#             return entrees[0].checktime.time(), None, 'pas_sortie', liste_bruts_complet
#         else:
#             return tries[0].checktime.time(), None, 'pas_sortie', liste_bruts_complet

#     premier = tries[0]
#     dernier = tries[-1]
#     ecart_minutes = (dernier.checktime - premier.checktime).total_seconds() / 60.0

#     # ── Cas 2 : écart total insuffisant (< 30 min) → doublon ─────────────
#     if ecart_minutes < seuil_minutes:
#         if sorties and not entrees:
#             return None, sorties[0].checktime.time(), 'pas_entree', liste_bruts_complet
#         return premier.checktime.time(), None, 'pas_sortie', liste_bruts_complet

#     # ── Cas 3 : plus de 2 pointages avec écart total >= 30 min ───────────
#     if len(tries) > 2:
#         filtres = [tries[0]]
#         for p in tries[1:]:
#             ecart = (p.checktime - filtres[-1].checktime).total_seconds() / 60.0
#             if ecart >= 15:
#                 filtres.append(p)

#         liste_bruts_filtres = [
#             {'time': p.checktime.time().strftime('%H:%M'), 'checktype': p.checktype.upper()}
#             for p in filtres
#         ]

#         if len(filtres) == 1:
#             if filtres[0].checktype.upper() == 'I':
#                 return None, filtres[0].checktime.time(), 'pas_entree', liste_bruts_filtres
#             else:
#                 return filtres[0].checktime.time(), None, 'pas_sortie', liste_bruts_filtres

#         if len(filtres) == 2:
#             heure_entree_brute = filtres[0].checktime.time()
#             heure_sortie_brute = filtres[-1].checktime.time()
            
#             # ⚠️ NOUVELLE LOGIQUE POUR L'ENTRÉE
#             heure_entree_corrigee = heure_entree_brute
#             if heure_entree_prevue and heure_entree_brute:
#                 # Calculer l'écart en minutes
#                 ref = datetime.today().date()
#                 dt_brute = datetime.combine(ref, heure_entree_brute)
#                 dt_prevue = datetime.combine(ref, heure_entree_prevue)
#                 ecart_entree_minutes = (dt_prevue - dt_brute).total_seconds() / 60.0
                
#                 # Si l'employé arrive plus d'1h avant → anomalie
#                 # if ecart_entree_minutes > 60:
#                 #     # On garde l'heure brute et on marque l'anomalie
#                 #     heure_entree_corrigee = heure_entree_brute
#                 #     type_anomalie_entree = 'entree_trop_tot'
#                 # else:
#                 #     # Règle normale : si avant l'heure prévue, on prend l'heure prévue
#                 #     if heure_entree_brute <= heure_entree_prevue:
#                 #         heure_entree_corrigee = heure_entree_prevue
#                 #         type_anomalie_entree = None
#                 #     else:
#                 #         heure_entree_corrigee = heure_entree_brute
#                 #         type_anomalie_entree = None
#                 if heure_entree_brute <= heure_entree_prevue:
#                     heure_entree_corrigee = heure_entree_prevue
#                 type_anomalie_entree = None
#             else:
#                 type_anomalie_entree = None
            
#             # Règle pour la sortie (inchangée)
#             heure_sortie_corrigee, retard_sortie = _choisir_heure_sortie(
#                 heure_sortie_brute, heure_sortie_prevue
#             )
            
#             # Déterminer le type d'anomalie final (priorité à entrée_trop_tot)
#             if type_anomalie_entree == 'entree_trop_tot':
#                 return heure_entree_corrigee, heure_sortie_corrigee, 'entree_trop_tot', liste_bruts_filtres
#             elif retard_sortie:
#                 return heure_entree_corrigee, heure_sortie_corrigee, 'retard_sortie', liste_bruts_filtres
#             else:
#                 return heure_entree_corrigee, heure_sortie_corrigee, None, liste_bruts_filtres

#         return filtres[0].checktime.time(), filtres[-1].checktime.time(), 'multiples_pointages', liste_bruts_filtres

#     # ── Cas 4 : exactement 2 pointages, écart >= 30 min ──────────────────
#     heure_entree_brute = premier.checktime.time()
#     heure_sortie_brute = dernier.checktime.time()
    
#     # ⚠️ NOUVELLE LOGIQUE POUR L'ENTRÉE (cas 2 pointages)
#     heure_entree_corrigee = heure_entree_brute
#     type_anomalie_entree = None
#     if heure_entree_prevue and heure_entree_brute:
#         ref = datetime.today().date()
#         dt_brute = datetime.combine(ref, heure_entree_brute)
#         dt_prevue = datetime.combine(ref, heure_entree_prevue)
#         ecart_entree_minutes = (dt_prevue - dt_brute).total_seconds() / 60.0
        
#         # if ecart_entree_minutes > 60:
#         #     heure_entree_corrigee = heure_entree_brute
#         #     type_anomalie_entree = 'entree_trop_tot'
#         # else:
#         #     if heure_entree_brute <= heure_entree_prevue:
#         #         heure_entree_corrigee = heure_entree_prevue
#         #     else:
#         #         heure_entree_corrigee = heure_entree_brute
#         if heure_entree_brute <= heure_entree_prevue:
#             heure_entree_corrigee = heure_entree_prevue
#         type_anomalie_entree = None
    
#     # Règle pour la sortie (inchangée)
#     heure_sortie_corrigee, retard_sortie = _choisir_heure_sortie(
#         heure_sortie_brute, heure_sortie_prevue
#     )
    
#     if type_anomalie_entree == 'entree_trop_tot':
#         return heure_entree_corrigee, heure_sortie_corrigee, 'entree_trop_tot', liste_bruts_complet
#     elif retard_sortie:
#         return heure_entree_corrigee, heure_sortie_corrigee, 'retard_sortie', liste_bruts_complet
#     else:
#         return heure_entree_corrigee, heure_sortie_corrigee, None, liste_bruts_complet

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
    sorties = [p for p in tries if p.checktype.upper() == 'I']

    # ── Cas 1 : un seul pointage ──────────────────────────────────────────
    if len(tries) == 1:
        if sorties and not entrees:
            return None, sorties[0].checktime.time(), 'pas_entree', liste_bruts_complet
        elif entrees:
            return entrees[0].checktime.time(), None, 'pas_sortie', liste_bruts_complet
        else:
            return tries[0].checktime.time(), None, 'pas_sortie', liste_bruts_complet

    premier = tries[0]
    dernier = tries[-1]
    ecart_minutes = (dernier.checktime - premier.checktime).total_seconds() / 60.0

    # ── Cas 2 : écart total insuffisant (< 30 min) → doublon ─────────────
    if ecart_minutes < seuil_minutes:
        if sorties and not entrees:
            return None, sorties[0].checktime.time(), 'pas_entree', liste_bruts_complet
        return premier.checktime.time(), None, 'pas_sortie', liste_bruts_complet

    # def _corriger_entree(heure_brute, heure_prevue):
    #     """Prend l'heure prévue si brute est dans les 15 min autour (avant ou après)."""
    #     if not heure_prevue or not heure_brute:
    #         return heure_brute
    #     ref = datetime.today().date()
    #     diff = (datetime.combine(ref, heure_brute) - datetime.combine(ref, heure_prevue)).total_seconds() / 60.0
    #     # brute avant l'heure prévue OU jusqu'à 15 min après → heure prévue
    #     if diff <= 15:
    #         return heure_prevue
    #     return heure_brute
    def _corriger_entree(heure_brute, heure_prevue):
        """Prend l'heure prévue si brute est dans les 15 min autour (avant ou après)."""
        if not heure_prevue or not heure_brute:
            return heure_brute
        ref = datetime.today().date()
        diff = (datetime.combine(ref, heure_brute) - datetime.combine(ref, heure_prevue)).total_seconds() / 60.0
        if diff <= 15:
            return heure_prevue
        return heure_brute.replace(second=0, microsecond=0)

    # ── Cas 3 : plus de 2 pointages avec écart total >= 30 min ───────────
    if len(tries) > 2:
        filtres = [tries[0]]
        for p in tries[1:]:
            ecart = (p.checktime - filtres[-1].checktime).total_seconds() / 60.0
            if ecart >= 15:
                filtres.append(p)

        liste_bruts_filtres = [
            {'time': p.checktime.time().strftime('%H:%M'), 'checktype': p.checktype.upper()}
            for p in filtres
        ]

        if len(filtres) == 1:
            if filtres[0].checktype.upper() == 'I':
                return None, filtres[0].checktime.time(), 'pas_entree', liste_bruts_filtres
            else:
                return filtres[0].checktime.time(), None, 'pas_sortie', liste_bruts_filtres

        if len(filtres) == 2:
            heure_entree_brute = filtres[0].checktime.time()
            heure_sortie_brute = filtres[-1].checktime.time()

            heure_entree_corrigee = _corriger_entree(heure_entree_brute, heure_entree_prevue)
            heure_sortie_corrigee, retard_sortie = _choisir_heure_sortie(
                heure_sortie_brute, heure_sortie_prevue
            )

            if retard_sortie:
                return heure_entree_corrigee, heure_sortie_corrigee, 'retard_sortie', liste_bruts_filtres
            return heure_entree_corrigee, heure_sortie_corrigee, None, liste_bruts_filtres

        #return filtres[0].checktime.time(), filtres[-1].checktime.time(), 'multiples_pointages', liste_bruts_filtres
        heure_entree_brute = filtres[0].checktime.time()
        heure_sortie_brute = filtres[-1].checktime.time()

        heure_entree_corrigee = _corriger_entree(heure_entree_brute, heure_entree_prevue)
        heure_sortie_corrigee, _ = _choisir_heure_sortie(heure_sortie_brute, heure_sortie_prevue)

        return heure_entree_corrigee, heure_sortie_corrigee, 'multiples_pointages', liste_bruts_filtres

    # ── Cas 4 : exactement 2 pointages, écart >= 30 min ──────────────────
    heure_entree_brute = premier.checktime.time()
    heure_sortie_brute = dernier.checktime.time()

    heure_entree_corrigee = _corriger_entree(heure_entree_brute, heure_entree_prevue)
    heure_sortie_corrigee, retard_sortie = _choisir_heure_sortie(
        heure_sortie_brute, heure_sortie_prevue
    )

    if retard_sortie:
        return heure_entree_corrigee, heure_sortie_corrigee, 'retard_sortie', liste_bruts_complet
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






from django.db.models import Q

def get_active_badgenumbers():
    from personnel.models import InformationPersonnelle

    return list(
        InformationPersonnelle.objects.filter(
            Q(depart__isnull=True) | Q(depart='') | Q(depart='0')
        ).values_list('numero_matricule', flat=True)
    )
# def get_active_badgenumbers():
#     from personnel.models import InformationPersonnelle
#     from django.db.models import Q
    
#     actifs = list(
#         InformationPersonnelle.objects.filter(
#             Q(depart__isnull=True) | Q(depart='') | Q(depart='0')
#         ).values_list('numero_matricule', flat=True)
#     )
    
#     # Si InformationPersonnelle est vide, utiliser directement UserInfo
#     if not actifs:
#         from presence.models import UserInfo
#         return list(UserInfo.objects.values_list('badgenumber', flat=True))
    
#     return actifs


def get_active_userinfo_queryset():
    from presence.models import UserInfo

    active_badges = get_active_badgenumbers()
    return UserInfo.objects.filter(badgenumber__in=active_badges)





def get_horaire_pour_date(horaire_section, date_jour, est_jour_paiement,
                           section=None):
    """
    Retourne (heure_entree: time, heure_sortie: time) en tenant compte :
    1. D'une HoraireException pour ce jour (globale ou par section)
    2. Des règles samedi / vendredi paiement / samedi paiement
    3. De l'horaire de section par défaut
    """
    from .models import HoraireException
    from datetime import time as dtime

    est_samedi   = date_jour.weekday() == 5
    est_vendredi = date_jour.weekday() == 4

    # ── 1. Chercher une exception spécifique à la section ──────────────────
    exception = None
    if section:
        exception = HoraireException.objects.filter(
            date=date_jour, section=section
        ).first()
    # ── 2. Sinon exception globale (section=None) ───────────────────────────
    if not exception:
        exception = HoraireException.objects.filter(
            date=date_jour, section__isnull=True
        ).first()

    # ── 3. Appliquer l'exception si trouvée ────────────────────────────────
    if exception:
        entree = exception.heure_entree or decimal_to_time(horaire_section.heure_entree)
        sortie = exception.heure_sortie or decimal_to_time(horaire_section.heure_sortie)
        return entree, sortie

    # ── 4. Logique habituelle ───────────────────────────────────────────────
    entree = decimal_to_time(horaire_section.heure_entree)

    if est_jour_paiement and est_vendredi:
        sortie = decimal_to_time(horaire_section.sortie_vendredi_paiement)
    elif est_jour_paiement and est_samedi:
        sortie = decimal_to_time(horaire_section.sortie_samedi_paiement)
    elif est_samedi:
        sortie = decimal_to_time(horaire_section.sortie_samedi)
    else:
        sortie = decimal_to_time(horaire_section.heure_sortie)

    return entree, sortie




def get_appellation_map():
    """
    Retourne {badgenumber: appellation} depuis InformationPersonnelle.
    Fallback sur nom_complet si appellation est vide.
    """
    from personnel.models import InformationPersonnelle
    return {
        emp.numero_matricule: emp.appellation or emp.nom_complet
        for emp in InformationPersonnelle.objects.only(
            'numero_matricule', 'appellation', 'nom_complet'
        )
    }







def get_periode_dates(annee: int, mois: int):
    """
    Retourne (debut_periode: date, fin_periode: date) en tenant compte
    des fermetures anticipées (PeriodeFermeture).
    """
    from presence.models import PeriodeFermeture

    if mois == 1:
        annee_prec, mois_prec = annee - 1, 12
    else:
        annee_prec, mois_prec = annee, mois - 1

    try:
        fp = PeriodeFermeture.objects.get(annee=annee_prec, mois=mois_prec)
        from datetime import date as d_cls, timedelta as td
        debut = fp.date_fermeture + td(days=1)
    except PeriodeFermeture.DoesNotExist:
        from datetime import date as d_cls
        debut = d_cls(annee_prec, mois_prec, 21)

    try:
        fc = PeriodeFermeture.objects.get(annee=annee, mois=mois)
        fin = fc.date_fermeture
    except PeriodeFermeture.DoesNotExist:
        from datetime import date as d_cls
        fin = d_cls(annee, mois, 20)

    return debut, fin
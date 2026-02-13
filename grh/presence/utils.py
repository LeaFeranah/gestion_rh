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
        # Convertir en float
        heure_decimal = float(heure_decimal)
        
        # Extraire la partie entière (heures)
        heures = int(heure_decimal)
        
        # Extraire la partie décimale (centièmes d'heure)
        centiemes = heure_decimal - heures  # Ex: 7.50 -> 0.50
        
        # Convertir les centièmes en minutes
        # 1 centième d'heure = 0.6 minute (car 100 centièmes = 60 minutes)
        minutes_fraction = centiemes * 100 * 0.6  # 0.50 * 100 * 0.6 = 30 minutes
        minutes = int(round(minutes_fraction))
        
        # Gérer les arrondis (si minutes == 60)
        if minutes >= 60:
            heures += 1
            minutes = 0
        
        # Normaliser les heures (0-23)
        heures = heures % 24
        
        return time(heures, minutes)
        
    except (ValueError, TypeError, AttributeError) as e:
        logger.error(f"Erreur dans decimal_to_time: {heure_decimal}, type: {type(heure_decimal)}, erreur: {e}")
        return None


def time_to_decimal(time_obj):
    """
    Convertit un objet time en décimal (format heures.centièmes)
    Ex: time(7, 30) -> 7.50, time(17, 50) -> 17.83
    """
    if time_obj is None:
        return None
    
    try:
        heures = time_obj.hour
        minutes = time_obj.minute
        
        # Convertir les minutes en centièmes d'heure
        # 60 minutes = 100 centièmes, donc 1 minute = 100/60 centièmes
        centiemes = (minutes * 100) / 60
        
        # Arrondir à 2 décimales
        decimal_value = heures + (centiemes / 100)
        return Decimal(str(round(decimal_value, 2)))
        
    except Exception as e:
        logger.error(f"Erreur dans time_to_decimal: {time_obj}, erreur: {e}")
        return None


def calculer_retard_entree(heure_reelle, heure_prevue, tolerance_minutes=20):
    """
    Calcule le retard à l'entrée
    
    Règles:
    - Si arrivée dans les 20 min de tolérance : pas de retard
    - Si arrivée en avance : pas de retard
    - Si retard > 20 min : retard = heure réelle - heure prévue
    
    Retourne: (minutes de retard, heure à comptabiliser)
    """
    if heure_reelle is None or heure_prevue is None:
        return 0, heure_reelle
    
    try:
        # Convertir en datetime pour faciliter les calculs
        today = datetime.today().date()
        dt_reelle = datetime.combine(today, heure_reelle)
        dt_prevue = datetime.combine(today, heure_prevue)
        
        # Calculer la différence
        diff = dt_reelle - dt_prevue
        diff_minutes = diff.total_seconds() / 60
        
        # Si en avance ou dans la tolérance
        if diff_minutes <= tolerance_minutes:
            return 0, heure_prevue
        
        # Si retard > tolérance
        retard_minutes = diff_minutes - tolerance_minutes
        return int(retard_minutes), heure_reelle
        
    except Exception as e:
        logger.error(f"Erreur dans calculer_retard_entree: {e}")
        return 0, heure_reelle

def calculer_sortie_anticipee(heure_reelle, heure_prevue, tolerance_minutes=5):
    """
    Calcule la sortie anticipée avec tolérance
    
    Règles:
    - Si sortie dans les 5 min avant l'heure prévue : pas de sortie anticipée, on compte l'heure prévue
    - Si sortie avant l'heure avec plus de 5 min d'avance : sortie anticipée = heure prévue - heure réelle
    - Si sortie après l'heure : pas de sortie anticipée
    
    Args:
        heure_reelle: time - heure de sortie réelle
        heure_prevue: time - heure de sortie prévue
        tolerance_minutes: int - tolérance en minutes (par défaut 5)
    
    Retourne: (minutes de sortie anticipée, heure à comptabiliser)
    """
    if heure_reelle is None or heure_prevue is None:
        return 0, heure_reelle
    
    try:
        today = datetime.today().date()
        dt_reelle = datetime.combine(today, heure_reelle)
        dt_prevue = datetime.combine(today, heure_prevue)
        
        # Calculer la différence (positif = en avance, négatif = en retard)
        diff = dt_prevue - dt_reelle
        diff_minutes = diff.total_seconds() / 60
        
        # Si sortie dans la tolérance (0 à 5 min avant) ou après l'heure prévue
        if diff_minutes <= tolerance_minutes:
            # Pas de sortie anticipée, on comptabilise l'heure prévue
            return 0, heure_prevue
        
        # Si sortie en avance de plus de 5 minutes
        if diff_minutes > tolerance_minutes:
            # Calculer la sortie anticipée (en excluant la tolérance)
            sortie_anticipee = int(diff_minutes - tolerance_minutes)
            return sortie_anticipee, heure_reelle
        
        # Par défaut (ne devrait jamais arriver)
        return 0, heure_prevue
        
    except Exception as e:
        logger.error(f"Erreur dans calculer_sortie_anticipee: {e}")
        return 0, heure_reelle



def calculer_heures_travaillees(heure_entree, heure_sortie, pause_minutes=60):
    """
    Calcule le nombre d'heures travaillées (en heures décimales)
    
    Args:
        heure_entree: objet time
        heure_sortie: objet time
        pause_minutes: durée de la pause en minutes (par défaut 60)
    
    Retourne: heures travaillées en décimal
    """
    if heure_entree is None or heure_sortie is None:
        return Decimal('0')
    
    try:
        today = datetime.today().date()
        dt_entree = datetime.combine(today, heure_entree)
        dt_sortie = datetime.combine(today, heure_sortie)
        
        # Vérifier que l'entrée est avant la sortie
        if dt_sortie <= dt_entree:
            return Decimal('0')
        
        # Calculer la différence
        diff = dt_sortie - dt_entree
        minutes_totales = diff.total_seconds() / 60
        
        # Soustraire la pause
        minutes_travaillees = minutes_totales - pause_minutes
        
        if minutes_travaillees < 0:
            return Decimal('0')
        
        # Convertir en heures décimales (arrondi à 2 décimales)
        heures = minutes_travaillees / 60
        return Decimal(str(round(heures, 2)))
        
    except Exception as e:
        logger.error(f"Erreur dans calculer_heures_travaillees: {e}")
        return Decimal('0')


def analyser_presence(heure_entree_reelle, heure_sortie_reelle, heure_entree_prevue, 
                      heure_sortie_prevue, date_pointage):
    """
    Analyse complète d'une présence
    
    Args:
        heure_entree_reelle: time - heure d'entrée réelle
        heure_sortie_reelle: time - heure de sortie réelle
        heure_entree_prevue: time - heure d'entrée prévue
        heure_sortie_prevue: time - heure de sortie prévue (ajustée si samedi)
        date_pointage: date - date du pointage
    
    Retourne: dict avec toutes les informations calculées
    """
    try:
        # Calculer retard entrée
        retard_minutes, heure_entree_comptabilisee = calculer_retard_entree(
            heure_entree_reelle, heure_entree_prevue
        )
        
        # Calculer sortie anticipée
        sortie_anticipee_minutes, heure_sortie_comptabilisee = calculer_sortie_anticipee(
            heure_sortie_reelle, heure_sortie_prevue
        )
        
        # Calculer heures travaillées
        heures_travaillees = calculer_heures_travaillees(
            heure_entree_comptabilisee, heure_sortie_comptabilisee
        )
        
        # Calculer heures prévues
        heures_prevues = calculer_heures_travaillees(
            heure_entree_prevue, heure_sortie_prevue
        )
        
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


def get_section_employe(badgenumber):
    """
    Récupère la section d'un employé via son badgenumber
    en interrogeant la base personnel
    """
    try:
        from personnel.models import InformationPersonnelle
        
        employe = InformationPersonnelle.objects.select_related(
            'information_professionnelle'
        ).get(numero_matricule=badgenumber)
        
        if hasattr(employe, 'information_professionnelle'):
            return employe.information_professionnelle.section
        
        return 'ADMINISTRATION'  # Section par défaut
    except Exception as e:
        logger.warning(f"Section non trouvée pour {badgenumber}: {e}")
        return 'ADMINISTRATION'  # Section par défaut si non trouvé


def format_duree(minutes):
    """
    Formate une durée en minutes en format "Xh Ymin"
    """
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
    """
    Calcule les heures supplémentaires
    """
    try:
        if heures_travaillees > heures_contractuelles:
            return heures_travaillees - heures_contractuelles
        return Decimal('0')
    except Exception:
        return Decimal('0')


def est_jour_ferie(date_pointage):
    """
    Vérifie si une date est un jour férié
    À implémenter selon votre logique métier
    """
    # TODO: Implémenter la logique des jours fériés
    return False





def corriger_pointages_automatique(pointages_bruts, heure_entree_prevue, heure_sortie_prevue):
    """
    Corrige automatiquement les inversions de pointages (O/I) et applique les règles de retard/avance
    
    Règles:
    1. Tous les pointages sont triés par heure
    2. Le premier pointage (le plus tôt) = entrée
    3. Le dernier pointage (le plus tard) = sortie
    4. Applique les règles:
       - Entrée en avance → heure prévue
       - Entrée en retard → heure brute
       - Sortie anticipée → heure brute
       - Sortie en retard → heure prévue
    
    Args:
        pointages_bruts: liste de CheckInOut (checktime, checktype)
        heure_entree_prevue: time - heure d'entrée prévue
        heure_sortie_prevue: time - heure de sortie prévue
        
    Returns:
        tuple: (heure_entree_corrigee, heure_sortie_corrigee, heures_corrigees_auto)
    """
    if not pointages_bruts:
        return None, None, False
    
    # Trier tous les pointages par heure (ignorer le type O/I)
    pointages_tries = sorted(pointages_bruts, key=lambda p: p.checktime)
    
    # Le premier pointage est l'entrée, le dernier est la sortie
    heure_entree_brute = pointages_tries[0].checktime.time()
    heure_sortie_brute = pointages_tries[-1].checktime.time() if len(pointages_tries) > 1 else None
    
    # Si un seul pointage, considérer comme entrée
    if len(pointages_tries) == 1:
        return heure_entree_brute, None, True
    
    # Appliquer les règles de retard/avance
    heure_entree_corrigee = None
    heure_sortie_corrigee = None
    heures_corrigees_auto = False
    
    # RÈGLE ENTRÉE
    if heure_entree_brute <= heure_entree_prevue:
        # Arrivée en avance → heure prévue
        heure_entree_corrigee = heure_entree_prevue
        heures_corrigees_auto = True
    else:
        # Arrivée en retard → heure brute
        heure_entree_corrigee = heure_entree_brute
    
    # RÈGLE SORTIE
    if heure_sortie_brute:
        if heure_sortie_brute < heure_sortie_prevue:
            # Sortie anticipée → heure brute
            heure_sortie_corrigee = heure_sortie_brute
            heures_corrigees_auto = True
        else:
            # Sortie en retard → heure prévue
            heure_sortie_corrigee = heure_sortie_prevue
    
    return heure_entree_corrigee, heure_sortie_corrigee, heures_corrigees_auto
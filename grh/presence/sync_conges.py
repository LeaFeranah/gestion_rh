# presence/sync_conges.py
"""
Synchronisation Access (table dbo_congevalides) -> PostgreSQL (table conge_valide).
  - Access est la RÉFÉRENCE : chaque passage relit toute la table Access.
  - Nouveau congé dans Access  -> créé ; modifié -> mis à jour ; supprimé -> supprimé.
  - La case « Validé » (valide / valide_par / valide_le) n'est jamais écrasée.
"""
import hashlib
import os
from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import transaction
from django.utils import timezone

DEFAULT_ACCESS_FILE = r"C:\Users\admin\Desktop\Grand_projet_rh\DEV\Personnel.accdb"
DEFAULT_ACCESS_TABLE = "dbo_congevalides"

# Colonne Access (en minuscules)  ->  champ du modèle CongeValide
COLONNES = {
    'matricule': 'matricule',
    'datedepart': 'date_depart',
    'heuredepart': 'heure_depart',
    'dateretour': 'date_retour',
    'heureretour': 'heure_retour',
    'duree': 'duree',
    'motif': 'motif',
    'justificatif': 'justificatif',
    'datevalidation': 'date_validation',
    'typeabsence': 'type_absence',
}


class SyncCongesError(Exception):
    pass


def get_config():
    cfg = getattr(settings, 'ACCESS_CONGES', {}) or {}
    return (cfg.get('file') or DEFAULT_ACCESS_FILE,
            cfg.get('table') or DEFAULT_ACCESS_TABLE)


# ── Conversions Access -> Python ────────────────────────────────────────────

def to_date(v):
    if v is None or v == '':
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    s = str(v).strip()
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y %H:%M:%S',
                '%Y-%m-%d %H:%M:%S', '%d/%m/%y'):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def to_time(v):
    if v is None or v == '':
        return None
    if isinstance(v, datetime):          # Access stocke l'heure en 1899-12-30 08:00
        return v.time().replace(microsecond=0)
    if isinstance(v, time):
        return v
    if isinstance(v, (int, float, Decimal)):
        f = float(v)
        if 0 <= f < 1:                   # fraction de journée
            return (datetime.min + timedelta(seconds=round(f * 86400))).time()
        if 0 <= f < 24:                  # heure décimale (8.5 = 08:30)
            return (datetime.min + timedelta(seconds=round(f * 3600))).time()
        return None
    s = str(v).strip().lower().replace('h', ':')
    if s.endswith(':'):
        s += '00'
    for fmt in ('%H:%M', '%H:%M:%S', '%d/%m/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(s, fmt).time()
        except ValueError:
            continue
    return None


def to_decimal(v):
    if v is None or v == '':
        return None
    try:
        return Decimal(str(v).strip().replace(',', '.')).quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError):
        return None


def to_text(v):
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def norm_matricule(v):
    s = str(v or '').strip()
    if s.endswith('.0') and s[:-2].isdigit():   # matricule numérique lu en float
        s = s[:-2]
    return s


def calcule_cle(d):
    """Identifiant stable d'un congé : matricule + départ + type d'absence."""
    brut = '|'.join([
        d['matricule'],
        d['date_depart'].isoformat() if d['date_depart'] else '',
        d['heure_depart'].strftime('%H:%M') if d['heure_depart'] else '',
        (d['type_absence'] or '').upper(),
    ])
    return hashlib.sha1(brut.encode('utf-8')).hexdigest()


# ── Lecture Access ──────────────────────────────────────────────────────────

def connecter_access(access_file):
    try:
        import pyodbc
    except ImportError:
        raise SyncCongesError("pyodbc n'est pas installé : pip install pyodbc")
    if not os.path.exists(access_file):
        raise SyncCongesError(f"Fichier Access introuvable : {access_file}")
    conn_str = (r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
                f'DBQ={access_file};')
    try:
        return pyodbc.connect(conn_str, readonly=True)
    except Exception as e:
        raise SyncCongesError(f"Connexion Access impossible : {e}")


def lire_access(access_file, table):
    conn = connecter_access(access_file)
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM [{table}]")
        noms = [c[0].lower() for c in cur.description]
        manquantes = [c for c in ('matricule', 'datedepart') if c not in noms]
        if manquantes:
            raise SyncCongesError(
                f"Colonnes absentes de [{table}] : {', '.join(manquantes)}. "
                f"Colonnes trouvées : {', '.join(noms)}")
        lignes = []
        for row in cur.fetchall():
            brut = dict(zip(noms, row))
            lignes.append({champ: brut.get(col) for col, champ in COLONNES.items()})
        return lignes
    finally:
        conn.close()


def nettoyer(brut):
    return {
        'matricule': norm_matricule(brut['matricule']),
        'date_depart': to_date(brut['date_depart']),
        'heure_depart': to_time(brut['heure_depart']),
        'date_retour': to_date(brut['date_retour']),
        'heure_retour': to_time(brut['heure_retour']),
        'duree': to_text(brut['duree']),
        'motif': to_text(brut['motif']),
        'justificatif': to_text(brut['justificatif']),
        'date_validation': to_date(brut['date_validation']),
        'type_absence': to_text(brut['type_absence']),
    }


# ── Synchronisation ─────────────────────────────────────────────────────────

CHAMPS_SOURCE = list(COLONNES.values())


def synchroniser_conges(access_file=None, table=None, dry_run=False,
                        supprimer=True, lignes=None):
    from .models import CongeValide

    f_def, t_def = get_config()
    access_file, table = access_file or f_def, table or t_def

    if lignes is None:
        lignes = lire_access(access_file, table)

    source, ignorees = {}, 0
    for brut in lignes:
        d = nettoyer(brut)
        if not d['matricule'] or not d['date_depart']:
            ignorees += 1
            continue
        source[calcule_cle(d)] = d

    existants = {c.cle_access: c for c in CongeValide.objects.all()}
    a_creer, a_maj = [], []
    for cle, d in source.items():
        obj = existants.get(cle)
        if obj is None:
            a_creer.append(CongeValide(cle_access=cle, **d))
        elif any(getattr(obj, k) != v for k, v in d.items()):
            for k, v in d.items():
                setattr(obj, k, v)
            a_maj.append(obj)

    # Sécurité : si Access ne renvoie rien, on ne vide pas PostgreSQL
    cles_a_supprimer = []
    if supprimer and source:
        cles_a_supprimer = [k for k in existants if k not in source]

    stats = {
        'lues': len(lignes),
        'ignorees': ignorees,
        'crees': len(a_creer),
        'mises_a_jour': len(a_maj),
        'supprimees': len(cles_a_supprimer),
        'total_access': len(source),
        'dry_run': dry_run,
    }
    if dry_run:
        return stats

    with transaction.atomic():
        if a_creer:
            CongeValide.objects.bulk_create(a_creer, batch_size=1000)
        if a_maj:
            for o in a_maj:
                o.synchronise_le = timezone.now()
            CongeValide.objects.bulk_update(a_maj, CHAMPS_SOURCE + ['synchronise_le'],
                                            batch_size=1000)
        if cles_a_supprimer:
            CongeValide.objects.filter(cle_access__in=cles_a_supprimer).delete()

    return stats
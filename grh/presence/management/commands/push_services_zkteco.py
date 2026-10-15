# presence/management/commands/push_services_zkteco.py
"""
Envoie les SERVICES de PostgreSQL (table departments) vers le logiciel ZKTeco
(SQL Server, base AttMgmt), et range chaque employé ZKTeco dans son service.

Sens : PostgreSQL (référence) ──► SQL Server (logiciel Att.exe)

  - Chaque service PostgreSQL est créé ou mis à jour dans DEPARTMENTS avec le
    MÊME numéro (deptid), pour que les deux systèmes parlent des mêmes services.
  - Le service n° 1 sert de racine (parent 0). Les services sans parent valide
    sont rangés sous lui.
  - Chaque employé ZKTeco (USERINFO) reçoit le service de l'employé PostgreSQL
    qui a le même numéro de badge. Badge inconnu → service racine n° 1.
  - Les services qui existent seulement dans ZKTeco ne sont pas supprimés.

Usage :
    python manage.py push_services_zkteco --dry-run   # simulation
    python manage.py push_services_zkteco             # applique
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from presence.management.commands.sync_zkteco import norm_badge

RACINE = 1
SMALLINT_MAX = 32767   # USERINFO.DEFAULTDEPTID est un smallint côté ZKTeco


class Command(BaseCommand):
    help = "Copie les services PostgreSQL vers le logiciel ZKTeco et y range les employés"

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help="Simulation : affiche ce qui serait fait, sans rien écrire")

    def handle(self, *args, **options):
        try:
            import pyodbc
        except ImportError:
            raise CommandError("pyodbc n'est pas installé : pip install pyodbc")
        conn_str = getattr(settings, 'ZKTECO_SQLSERVER', None)
        if not conn_str:
            raise CommandError("ZKTECO_SQLSERVER n'est pas défini dans settings.py")
        dry_run = options['dry_run']

        self.stdout.write("═" * 60)
        self.stdout.write(f"  SERVICES POSTGRESQL → ZKTECO{'  (DRY-RUN)' if dry_run else ''}")
        self.stdout.write("═" * 60)

        # ── 1. Lecture PostgreSQL ───────────────────────────────────────────
        with connection.cursor() as pg:
            pg.execute("SELECT deptid, deptname, supdeptid FROM departments ORDER BY deptid")
            services_pg = pg.fetchall()
            # badge -> service ; badge partagé : employé au pointage le plus récent
            pg.execute("""
                SELECT u.userid, u.badgenumber, u.defaultdeptid, MAX(c.checktime)
                FROM userinfo u LEFT JOIN checkinout c ON c.userid = u.userid
                GROUP BY u.userid, u.badgenumber, u.defaultdeptid
            """)
            candidats = {}
            for userid, badge, deptid, dernier in pg.fetchall():
                b = norm_badge(badge)
                if b:
                    candidats.setdefault(b, []).append((dernier is not None, dernier or 0, userid, deptid))
        badge_to_dept = {}
        for b, lst in candidats.items():
            lst.sort(key=lambda x: (x[0], x[1], x[2]))
            badge_to_dept[b] = lst[-1][3]

        ids_pg = {d[0] for d in services_pg}
        self.stdout.write(f"  PostgreSQL : {len(services_pg)} services, {len(badge_to_dept)} badges")

        # ── 2. Connexion SQL Server (écriture) ──────────────────────────────
        try:
            ms = pyodbc.connect(conn_str, autocommit=False, timeout=15)
        except pyodbc.Error as e:
            raise CommandError(f"Connexion SQL Server impossible : {e}")

        try:
            cur = ms.cursor()
            cur.fast_executemany = True
            longueur = cur.execute("SELECT COL_LENGTH('DEPARTMENTS', 'DEPTNAME')").fetchval()
            max_nom = 100 if not longueur or longueur < 0 else longueur // 2
            existants = {r[0] for r in cur.execute("SELECT DEPTID FROM DEPARTMENTS").fetchall()}

            # Services à écrire (même numéro qu'en PostgreSQL)
            lignes = []
            for deptid, nom, parent in services_pg:
                if deptid == RACINE:
                    parent = 0
                elif parent in (None, 0) or parent == deptid or parent not in ids_pg:
                    parent = RACINE
                nom = (nom or f"Service {deptid}").strip()[:max_nom]
                lignes.append((deptid, nom, parent))

            a_creer = [l for l in lignes if l[0] not in existants]
            a_modifier = [l for l in lignes if l[0] in existants]
            creer_racine = RACINE not in ids_pg and RACINE not in existants

            ids_finaux = existants | ids_pg | {RACINE}

            # Employés : service selon le badge
            employes = cur.execute("SELECT USERID, Badgenumber, DEFAULTDEPTID FROM USERINFO").fetchall()
            maj_employes, inconnus = [], 0
            for userid, badge, actuel in employes:
                dept = badge_to_dept.get(norm_badge(badge))
                if dept is None:
                    inconnus += 1
                if dept is None or dept not in ids_finaux or dept > SMALLINT_MAX:
                    dept = RACINE
                if dept != actuel:
                    maj_employes.append((dept, userid))

            self.stdout.write(f"  Services à créer dans ZKTeco : {len(a_creer) + (1 if creer_racine else 0)}")
            self.stdout.write(f"  Services à mettre à jour     : {len(a_modifier)}")
            self.stdout.write(f"  Employés ZKTeco              : {len(employes)} "
                              f"(dont {inconnus} badges absents de PostgreSQL → service racine)")
            self.stdout.write(f"  Employés à changer de service : {len(maj_employes)}")

            if dry_run:
                self.stdout.write(self.style.WARNING("  DRY-RUN : rien n'a été écrit."))
                return

            if creer_racine:
                a_creer.append((RACINE, "SOCIETE", 0))
            if a_creer:
                cur.execute("SET IDENTITY_INSERT DEPARTMENTS ON")
                cur.executemany("INSERT INTO DEPARTMENTS (DEPTID, DEPTNAME, SUPDEPTID) VALUES (?, ?, ?)", a_creer)
                cur.execute("SET IDENTITY_INSERT DEPARTMENTS OFF")
            if a_modifier:
                cur.executemany("UPDATE DEPARTMENTS SET DEPTNAME = ?, SUPDEPTID = ? WHERE DEPTID = ?",
                                [(n, p, i) for i, n, p in a_modifier])
            if maj_employes:
                cur.executemany("UPDATE USERINFO SET DEFAULTDEPTID = ? WHERE USERID = ?", maj_employes)
            ms.commit()
        except Exception as e:
            ms.rollback()
            raise CommandError(f"❌ Interrompu (rien n'a été modifié dans ZKTeco) : {e}")
        finally:
            ms.close()

        self.stdout.write(self.style.SUCCESS("  ✅ OK : services et employés mis à jour dans ZKTeco"))
# presence/management/commands/sync_zkteco.py
"""
Copie les POINTAGES du logiciel ZKTeco (SQL Server, base AttMgmt) vers PostgreSQL.

Principe :
  - Les employés (userinfo) et services (departments) de PostgreSQL sont la
    référence : ils ne sont JAMAIS modifiés par cette commande.
  - Chaque pointage SQL Server est rattaché à l'employé PostgreSQL qui a le
    MÊME NUMÉRO DE BADGE (Badgenumber), pas le même USERID, car les USERID
    internes du logiciel ZKTeco peuvent différer de ceux de PostgreSQL.
  - Les badges inconnus dans PostgreSQL sont ignorés et listés.

Usage :
    python manage.py sync_zkteco              # pointages des 60 derniers jours
    python manage.py sync_zkteco --jours 10   # fenêtre personnalisée
    python manage.py sync_zkteco --full       # tout l'historique
    python manage.py sync_zkteco --dry-run    # simulation, n'écrit rien

SQL Server est uniquement LU. Un pointage déjà présent dans PostgreSQL
(même userid + même checktime) n'est jamais dupliqué ni modifié.
"""
from collections import Counter

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

BATCH = 5000


def norm_badge(value):
    """Normalise un numéro de badge : espaces retirés, zéros de tête ignorés si numérique."""
    s = str(value or '').strip()
    return str(int(s)) if s.isdigit() else s.upper()


class Command(BaseCommand):
    help = "Copie les pointages ZKTeco (SQL Server) vers PostgreSQL en les reliant par numéro de badge"

    def add_arguments(self, parser):
        parser.add_argument('--full', action='store_true',
                            help="Importer tout l'historique des pointages")
        parser.add_argument('--jours', type=int, default=60,
                            help="Nombre de jours relus à chaque passage (défaut : 60)")
        parser.add_argument('--dry-run', action='store_true',
                            help="Simulation : affiche les volumes sans rien écrire")

    def handle(self, *args, **options):
        try:
            import pyodbc
        except ImportError:
            raise CommandError("pyodbc n'est pas installé : pip install pyodbc")

        conn_str = getattr(settings, 'ZKTECO_SQLSERVER', None)
        if not conn_str:
            raise CommandError("ZKTECO_SQLSERVER n'est pas défini dans settings.py")

        full, jours, dry_run = options['full'], options['jours'], options['dry_run']
        mode = "COMPLET" if full else f"{jours} derniers jours"
        self.stdout.write("═" * 60)
        self.stdout.write(f"  POINTAGES ZKTECO → POSTGRESQL  ({mode}{', DRY-RUN' if dry_run else ''})")
        self.stdout.write("═" * 60)

        # ── 1. Correspondance badge → userid PostgreSQL (référence) ─────────
        # Si un badge existe sur plusieurs userid, on garde celui qui a le
        # pointage le plus récent dans PostgreSQL (le circuit utilisé jusqu'ici),
        # sinon le userid le plus élevé (le plus récemment créé).
        with connection.cursor() as pg:
            pg.execute("""
                SELECT u.userid, u.badgenumber, MAX(c.checktime)
                FROM userinfo u LEFT JOIN checkinout c ON c.userid = u.userid
                GROUP BY u.userid, u.badgenumber
            """)
            candidats = {}
            for userid, badge, dernier in pg.fetchall():
                b = norm_badge(badge)
                if b:
                    candidats.setdefault(b, []).append((dernier, userid))

        badge_to_userid, doublons = {}, {}
        for b, lst in candidats.items():
            # tri : dernier pointage (None = jamais) puis userid, le plus grand gagne
            lst.sort(key=lambda x: (x[0] is not None, x[0] or 0, x[1]))
            badge_to_userid[b] = lst[-1][1]
            if len(lst) > 1:
                doublons[b] = [u for _, u in lst]

        self.stdout.write(f"  PostgreSQL : {len(badge_to_userid)} badges d'employés")
        if doublons:
            self.stdout.write(self.style.WARNING(
                f"  ⚠ {len(doublons)} badge(s) partagé(s) par plusieurs userid : "
                f"pointage attribué au userid le plus récemment pointé"))

        # ── 2. Lecture des pointages SQL Server ─────────────────────────────
        try:
            ms = pyodbc.connect(conn_str, readonly=True, timeout=15)
        except pyodbc.Error as e:
            raise CommandError(f"Connexion SQL Server impossible : {e}")

        sql = ("SELECT u.Badgenumber, c.CHECKTIME, c.CHECKTYPE "
               "FROM CHECKINOUT c JOIN USERINFO u ON u.USERID = c.USERID "
               "WHERE c.CHECKTIME <= DATEADD(day, 1, GETDATE())")   # ignore les dates aberrantes (ex. 2103)
        params = []
        if not full:
            sql += " AND c.CHECKTIME >= DATEADD(day, ?, GETDATE())"
            params.append(-jours)

        lus, rattaches, inconnus = 0, [], Counter()
        try:
            cur = ms.cursor()
            cur.execute(sql, params)
            while True:
                rows = cur.fetchmany(BATCH)
                if not rows:
                    break
                for badge, checktime, checktype in rows:
                    lus += 1
                    userid = badge_to_userid.get(norm_badge(badge))
                    if userid is None:
                        inconnus[str(badge).strip()] += 1
                        continue
                    rattaches.append((userid, checktime, (checktype or '')[:1]))
        finally:
            ms.close()

        self.stdout.write(f"  SQL Server : {lus} pointages lus")
        self.stdout.write(f"  Rattachés à un employé PostgreSQL : {len(rattaches)}")
        if inconnus:
            self.stdout.write(self.style.WARNING(
                f"  ⚠ {sum(inconnus.values())} pointages ignorés : {len(inconnus)} badge(s) "
                f"absent(s) de PostgreSQL"))
            for badge, n in inconnus.most_common(15):
                self.stdout.write(f"      badge {badge} : {n} pointages")

        if dry_run:
            self.stdout.write(self.style.WARNING("  DRY-RUN : rien n'a été écrit."))
            return

        # ── 3. Insertion des seuls nouveaux pointages ───────────────────────
        try:
            with transaction.atomic(), connection.cursor() as pg:
                pg.execute("CREATE INDEX IF NOT EXISTS idx_checkinout_user_time "
                           "ON checkinout (userid, checktime)")
                pg.execute("""
                    CREATE TEMP TABLE tmp_zk_checkinout (
                        userid int, checktime timestamp, checktype varchar(1)
                    ) ON COMMIT DROP
                """)
                for i in range(0, len(rattaches), BATCH):
                    pg.executemany("INSERT INTO tmp_zk_checkinout VALUES (%s, %s, %s)",
                                   rattaches[i:i + BATCH])
                pg.execute("""
                    INSERT INTO checkinout (userid, checktime, checktype)
                    SELECT DISTINCT ON (t.userid, t.checktime) t.userid, t.checktime, t.checktype
                    FROM tmp_zk_checkinout t
                    WHERE NOT EXISTS (
                        SELECT 1 FROM checkinout c
                        WHERE c.userid = t.userid AND c.checktime = t.checktime
                    )
                    ORDER BY t.userid, t.checktime
                """)
                nouveaux = pg.rowcount
        except Exception as e:
            raise CommandError(f"❌ Synchro interrompue (rien n'a été modifié) : {e}")

        self.stdout.write(self.style.SUCCESS(f"  ✅ OK : {nouveaux} nouveaux pointages ajoutés"))
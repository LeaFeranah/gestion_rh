# presence/management/commands/sync_conges_access.py
"""
Usage :
    python manage.py sync_conges_access                 # synchro normale
    python manage.py sync_conges_access --dry-run       # simulation
    python manage.py sync_conges_access --list-columns  # voir les colonnes Access
    python manage.py sync_conges_access --sans-suppression
"""
from django.core.management.base import BaseCommand, CommandError

from presence.sync_conges import (
    SyncCongesError, connecter_access, get_config, synchroniser_conges,
)


class Command(BaseCommand):
    help = "Synchronise les congés validés Access (dbo_congevalides) vers PostgreSQL"

    def add_arguments(self, parser):
        parser.add_argument('--access-file', type=str, help="Chemin du fichier .accdb/.mdb")
        parser.add_argument('--table', type=str, help="Nom de la table Access")
        parser.add_argument('--dry-run', action='store_true', help="Simulation, n'écrit rien")
        parser.add_argument('--sans-suppression', action='store_true',
                            help="Ne pas supprimer dans PostgreSQL les congés disparus d'Access")
        parser.add_argument('--list-columns', action='store_true',
                            help="Affiche les colonnes de la table Access et quitte")

    def handle(self, *args, **opt):
        f_def, t_def = get_config()
        access_file = opt.get('access_file') or f_def
        table = opt.get('table') or t_def

        self.stdout.write("═" * 60)
        self.stdout.write(f"  CONGÉS VALIDÉS ACCESS → POSTGRESQL"
                          f"{'  (DRY-RUN)' if opt['dry_run'] else ''}")
        self.stdout.write(f"  Fichier : {access_file}")
        self.stdout.write(f"  Table   : {table}")
        self.stdout.write("═" * 60)

        try:
            if opt['list_columns']:
                conn = connecter_access(access_file)
                try:
                    cur = conn.cursor()
                    cur.execute(f"SELECT TOP 1 * FROM [{table}]")
                    for c in cur.description:
                        self.stdout.write(f"   - {c[0]}  ({c[1].__name__ if c[1] else '?'})")
                finally:
                    conn.close()
                return

            stats = synchroniser_conges(
                access_file=access_file, table=table,
                dry_run=opt['dry_run'], supprimer=not opt['sans_suppression'],
            )
        except SyncCongesError as e:
            raise CommandError(f"❌ {e}")
        except Exception as e:
            raise CommandError(f"❌ Synchro interrompue (rien n'a été modifié) : {e}")

        self.stdout.write(f"  Lignes lues dans Access : {stats['lues']}")
        if stats['ignorees']:
            self.stdout.write(self.style.WARNING(
                f"  ⚠ {stats['ignorees']} ligne(s) ignorée(s) (matricule ou DateDepart vide)"))
        msg = (f"{stats['crees']} créé(s), {stats['mises_a_jour']} mis à jour, "
               f"{stats['supprimees']} supprimé(s)")
        if opt['dry_run']:
            self.stdout.write(self.style.WARNING(f"  DRY-RUN : {msg} (rien n'a été écrit)"))
        else:
            self.stdout.write(self.style.SUCCESS(f"  ✅ OK : {msg}"))
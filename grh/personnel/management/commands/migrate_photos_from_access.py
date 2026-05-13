import os
import pyodbc
import psycopg2
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Migre les photos depuis la base Access vers PostgreSQL'

    ACCESS_FILE = r"C:\Users\admin\Desktop\Grand_projet_rh\DEV\Personnel.accdb"
    ACCESS_TABLE = "dbo_personnels"
    ACCESS_MATRICULE_FIELD = "matricule"
    ACCESS_PHOTO_FIELD = "PHOTO"

    SIGNATURES = {
        b'\xff\xd8\xff': 'jpg',
        b'\x89PNG':      'png',
        b'GIF87a':       'gif',
        b'GIF89a':       'gif',
        b'BM':           'bmp',
    }

    def add_arguments(self, parser):
        parser.add_argument('--access-file', type=str)
        parser.add_argument('--access-table', type=str)
        parser.add_argument('--list-tables', action='store_true')
        parser.add_argument('--list-columns', type=str)  # ← NOUVEAU

    def handle(self, *args, **options):
        access_file = options.get('access_file') or self.ACCESS_FILE

        if not os.path.exists(access_file):
            self.stdout.write(self.style.ERROR(f"❌ Fichier Access non trouvé : {access_file}"))
            return

        conn_str = (
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            f'DBQ={access_file};'
        )

        try:
            access_conn = pyodbc.connect(conn_str)
            self.stdout.write(self.style.SUCCESS("✅ Connexion Access OK"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Connexion Access échouée : {e}"))
            return

        # ── Lister les tables ──────────────────────────────────────
        if options.get('list_tables'):
            cursor = access_conn.cursor()
            tables = [row.table_name for row in cursor.tables(tableType='TABLE')]
            self.stdout.write("\n📋 Tables disponibles dans Access :")
            for t in tables:
                self.stdout.write(f"   - {t}")
            access_conn.close()
            return

        # ── Lister les colonnes ────────────────────────────────────
        if options.get('list_columns'):
            table = options['list_columns']
            cursor = access_conn.cursor()
            cursor.execute(f"SELECT TOP 1 * FROM [{table}]")
            cols = [desc[0] for desc in cursor.description]
            self.stdout.write(f"\n📋 Colonnes de la table '{table}' :")
            for col in cols:
                self.stdout.write(f"   - {col}")
            access_conn.close()
            return

        # ── Migration des photos ───────────────────────────────────
        access_table = options.get('access_table') or self.ACCESS_TABLE

        self.stdout.write(f"\n🔍 Lecture de la table '{access_table}'...")

        access_cursor = access_conn.cursor()

        try:
            access_cursor.execute(
                f"SELECT {self.ACCESS_MATRICULE_FIELD}, {self.ACCESS_PHOTO_FIELD} "
                f"FROM {access_table} "
                f"WHERE {self.ACCESS_PHOTO_FIELD} IS NOT NULL"
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur requête Access : {e}"))
            access_cursor.execute(f"SELECT TOP 1 * FROM [{access_table}]")
            cols = [desc[0] for desc in access_cursor.description]
            self.stdout.write(f"📋 Colonnes disponibles : {cols}")
            access_conn.close()
            return

        rows = access_cursor.fetchall()
        self.stdout.write(f"📦 {len(rows)} photos trouvées dans Access\n")

        pg_conn = psycopg2.connect(
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT'],
        )
        pg_cursor = pg_conn.cursor()

        photos_dir = os.path.join(settings.MEDIA_ROOT, 'photos_employes')
        os.makedirs(photos_dir, exist_ok=True)

        success = 0
        not_found = 0
        errors = 0

        for row in rows:
            matricule = str(row[0]).strip()
            photo_data = row[1]

            try:
                if photo_data is None:
                    continue

                if isinstance(photo_data, bytearray):
                    data = bytes(photo_data)
                elif isinstance(photo_data, memoryview):
                    data = bytes(photo_data)
                elif isinstance(photo_data, bytes):
                    data = photo_data
                else:
                    self.stdout.write(self.style.WARNING(
                        f"⚠️  {matricule} - type inattendu : {type(photo_data)}"
                    ))
                    errors += 1
                    continue

                offset, extension = self._find_image_start(data)

                if offset is None:
                    self.stdout.write(self.style.WARNING(
                        f"⚠️  {matricule} - format non reconnu ({len(data)} bytes)"
                    ))
                    errors += 1
                    continue

                image_bytes = data[offset:]
                filename = f"emp_{matricule}.{extension}"
                filepath = os.path.join(photos_dir, filename)
                relative_path = f"photos_employes/{filename}"

                with open(filepath, 'wb') as f:
                    f.write(image_bytes)

                pg_cursor.execute("""
                    UPDATE personnel_informationpersonnelle
                    SET photo = %s
                    WHERE numero_matricule = %s
                """, (relative_path, matricule))

                if pg_cursor.rowcount == 0:
                    self.stdout.write(self.style.WARNING(
                        f"⚠️  {matricule} - pas trouvé dans PostgreSQL"
                    ))
                    not_found += 1
                    os.remove(filepath)
                else:
                    pg_conn.commit()
                    self.stdout.write(self.style.SUCCESS(
                        f"✅ {matricule} → {relative_path}"
                    ))
                    success += 1

            except Exception as e:
                pg_conn.rollback()
                self.stdout.write(self.style.ERROR(f"❌ {matricule} - {str(e)}"))
                errors += 1

        access_conn.close()
        pg_cursor.close()
        pg_conn.close()

        self._clear_blob_placeholders()

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(self.style.SUCCESS(f"✅ Migrés avec succès : {success}"))
        self.stdout.write(self.style.WARNING(f"⚠️  Non trouvés en PG  : {not_found}"))
        self.stdout.write(self.style.ERROR(f"❌ Erreurs            : {errors}"))

    def _find_image_start(self, data):
        for signature, extension in self.SIGNATURES.items():
            pos = data.find(signature)
            if pos != -1:
                return pos, extension
        return None, None

    def _clear_blob_placeholders(self):
        pg_conn = psycopg2.connect(
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT'],
        )
        cursor = pg_conn.cursor()
        cursor.execute("""
            UPDATE personnel_informationpersonnelle
            SET photo = NULL
            WHERE photo = '[BLOB]'
        """)
        count = cursor.rowcount
        pg_conn.commit()
        cursor.close()
        pg_conn.close()
        if count > 0:
            self.stdout.write(f"🧹 {count} placeholder(s) [BLOB] nettoyé(s)")
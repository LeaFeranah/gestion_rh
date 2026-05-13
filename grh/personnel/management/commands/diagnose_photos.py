import psycopg2
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Analyse les premiers bytes des photos BLOB'

    def handle(self, *args, **kwargs):
        conn = psycopg2.connect(
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT'],
        )
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, numero_matricule, photo
            FROM personnel_informationpersonnelle
            WHERE photo IS NOT NULL AND photo != ''
            LIMIT 5
        """)
        rows = cursor.fetchall()

        for emp_id, matricule, photo_data in rows:
            if isinstance(photo_data, memoryview):
                data = bytes(photo_data)
            elif isinstance(photo_data, str):
                data = photo_data.encode('latin-1')
            else:
                data = photo_data

            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"Matricule: {matricule} | Taille: {len(data)} bytes")
            self.stdout.write(f"Bytes 0-20   (hex): {data[0:20].hex()}")
            self.stdout.write(f"Bytes 0-20   (raw): {data[0:20]}")
            self.stdout.write(f"Bytes 70-90  (hex): {data[70:90].hex()}")
            self.stdout.write(f"Bytes 150-170(hex): {data[150:170].hex()}")

            # Chercher les magic bytes connus
            signatures = {
                b'\xff\xd8': 'JPEG',
                b'\x89PNG': 'PNG',
                b'BM':      'BMP',
                b'GIF':     'GIF',
            }
            for sig, name in signatures.items():
                pos = data.find(sig)
                if pos != -1:
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ {name} trouvé à l'offset {pos}")
                    )

        cursor.close()
        conn.close()
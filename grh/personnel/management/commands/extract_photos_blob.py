import os
import psycopg2
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Extrait les photos BLOB Access OLE et crée les fichiers images'

    # Signatures des formats images
    SIGNATURES = {
        b'\xff\xd8\xff': 'jpg',
        b'\x89PNG':      'png',
        b'GIF87a':       'gif',
        b'GIF89a':       'gif',
        b'BM':           'bmp',
        b'RIFF':         'webp',
    }

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
            AND photo NOT LIKE 'photos_employes/%%'
        """)
        rows = cursor.fetchall()

        self.stdout.write(f"🔍 {len(rows)} photos à traiter\n")

        photos_dir = os.path.join(settings.MEDIA_ROOT, 'photos_employes')
        os.makedirs(photos_dir, exist_ok=True)

        success = 0
        errors = 0
        offsets_found = {}  # Pour statistiques sur les offsets

        for emp_id, matricule, photo_data in rows:
            try:
                # Convertir en bytes
                if isinstance(photo_data, memoryview):
                    data = bytes(photo_data)
                elif isinstance(photo_data, str):
                    data = photo_data.encode('latin-1')
                else:
                    data = bytes(photo_data)

                # Trouver l'offset et le format
                offset, extension = self._find_image_start(data)

                if offset is None:
                    self.stdout.write(self.style.WARNING(
                        f"⚠️  {matricule} - aucun format image trouvé dans {len(data)} bytes"
                    ))
                    errors += 1
                    continue

                # Statistique des offsets
                offsets_found[offset] = offsets_found.get(offset, 0) + 1

                # Extraire les bytes image uniquement
                image_bytes = data[offset:]

                # Nom et chemin du fichier
                filename = f"emp_{matricule}.{extension}"
                filepath = os.path.join(photos_dir, filename)
                relative_path = f"photos_employes/{filename}"

                # Écrire le fichier
                with open(filepath, 'wb') as f:
                    f.write(image_bytes)

                # Vérifier que le fichier est valide (taille minimale)
                if os.path.getsize(filepath) < 100:
                    os.remove(filepath)
                    self.stdout.write(self.style.WARNING(
                        f"⚠️  {matricule} - fichier trop petit, ignoré"
                    ))
                    errors += 1
                    continue

                # Mettre à jour la DB
                cursor.execute("""
                    UPDATE personnel_informationpersonnelle
                    SET photo = %s
                    WHERE id = %s
                """, (relative_path, emp_id))
                conn.commit()

                self.stdout.write(self.style.SUCCESS(
                    f"✅ {matricule} → {relative_path} (offset={offset}, {extension})"
                ))
                success += 1

            except Exception as e:
                conn.rollback()
                self.stdout.write(self.style.ERROR(
                    f"❌ {matricule} - {str(e)}"
                ))
                errors += 1

        cursor.close()
        conn.close()

        # Résumé
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(self.style.SUCCESS(f"✅ Succès  : {success}"))
        self.stdout.write(self.style.ERROR(f"❌ Erreurs : {errors}"))
        if offsets_found:
            self.stdout.write(f"\n📊 Offsets détectés :")
            for offset, count in sorted(offsets_found.items()):
                self.stdout.write(f"   Offset {offset} : {count} photo(s)")

    def _find_image_start(self, data):
        """
        Cherche le début des données image dans le BLOB OLE Access.
        Retourne (offset, extension) ou (None, None).
        """
        for signature, extension in self.SIGNATURES.items():
            pos = data.find(signature)
            if pos != -1:
                # Pour WEBP, vérifier les bytes 8-12
                if signature == b'RIFF':
                    if len(data) > pos + 12 and data[pos+8:pos+12] == b'WEBP':
                        return pos, 'webp'
                    continue
                return pos, extension

        return None, None
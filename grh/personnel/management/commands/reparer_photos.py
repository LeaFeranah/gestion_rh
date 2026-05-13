# personnel/management/commands/reparer_photos.py

import os
from PIL import Image, ImageFile
import pyodbc
import psycopg2
from django.core.management.base import BaseCommand
from django.conf import settings
from personnel.models import InformationPersonnelle

ImageFile.LOAD_TRUNCATED_IMAGES = True

class Command(BaseCommand):
    help = 'Répare les 146 photos corrompues'

    ACCESS_FILE = r"C:\Users\admin\Desktop\Grand_projet_rh\DEV\Personnel.accdb"

    SIGNATURES = {
        b'\xff\xd8\xff': 'jpg',
        b'\x89PNG':      'png',
        b'GIF87a':       'gif',
        b'GIF89a':       'gif',
        b'BM':           'bmp',
    }

    def handle(self, *args, **kwargs):
        # Trouver les 146 corrompus
        corrompus = []
        employes = InformationPersonnelle.objects.exclude(photo=None).exclude(photo='')

        for emp in employes:
            path = os.path.join(settings.MEDIA_ROOT, str(emp.photo))
            if not os.path.exists(path):
                continue
            try:
                with Image.open(path) as img:
                    img.verify()
            except Exception:
                corrompus.append(emp.numero_matricule)

        print(f"🔍 {len(corrompus)} photos corrompues à réparer", flush=True)

        if not corrompus:
            print("✅ Aucune photo corrompue !")
            return

        # Connexion Access
        conn_str = (
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            f'DBQ={self.ACCESS_FILE};'
        )
        try:
            access_conn = pyodbc.connect(conn_str)
            print("✅ Connexion Access OK", flush=True)
        except Exception as e:
            print(f"❌ Connexion Access échouée : {e}", flush=True)
            return

        photos_dir = os.path.join(settings.MEDIA_ROOT, 'photos_employes')
        success = 0
        deleted = 0

        for matricule in corrompus:
            try:
                cursor = access_conn.cursor()
                cursor.execute(
                    "SELECT PHOTO FROM dbo_personnels WHERE matricule = ?",
                    (matricule,)
                )
                row = cursor.fetchone()

                if not row or row[0] is None:
                    self._supprimer_photo(matricule)
                    deleted += 1
                    print(f"🗑️  {matricule} - pas dans Access", flush=True)
                    continue

                photo_data = row[0]

                # Convertir en bytes
                if isinstance(photo_data, bytearray):
                    data = bytes(photo_data)
                elif isinstance(photo_data, memoryview):
                    data = bytes(photo_data)
                else:
                    data = bytes(photo_data)

                # Chercher TOUS les offsets possibles, pas juste le premier
                best_result = self._extraire_meilleure_image(data, matricule, photos_dir)

                if best_result:
                    emp = InformationPersonnelle.objects.get(numero_matricule=matricule)
                    # Supprimer l'ancien fichier corrompu
                    old_path = os.path.join(settings.MEDIA_ROOT, str(emp.photo))
                    if os.path.exists(old_path):
                        os.remove(old_path)
                    emp.photo = best_result
                    emp.save(update_fields=['photo'])
                    success += 1
                    print(f"✅ {matricule} → {best_result}", flush=True)
                else:
                    self._supprimer_photo(matricule)
                    deleted += 1
                    print(f"🗑️  {matricule} - irrécupérable", flush=True)

            except Exception as e:
                print(f"❌ {matricule} - {e}", flush=True)

        access_conn.close()

        print(f"\n{'='*50}", flush=True)
        print(f"✅ Réparés  : {success}", flush=True)
        print(f"🗑️  Supprimés : {deleted}", flush=True)

    def _extraire_meilleure_image(self, data, matricule, photos_dir):
        """Essaie tous les offsets pour trouver une image valide"""
        candidates = []

        # Trouver TOUS les offsets pour chaque signature
        for signature, extension in self.SIGNATURES.items():
            offset = 0
            while True:
                pos = data.find(signature, offset)
                if pos == -1:
                    break
                candidates.append((pos, extension))
                offset = pos + 1

        # Trier par offset
        candidates.sort(key=lambda x: x[0])

        for pos, extension in candidates:
            image_bytes = data[pos:]
            filename = f"emp_{matricule}.{extension}"
            filepath = os.path.join(photos_dir, filename)
            relative = f"photos_employes/{filename}"

            try:
                # Écrire et vérifier
                with open(filepath, 'wb') as f:
                    f.write(image_bytes)

                with Image.open(filepath) as img:
                    img.verify()

                # Vérifier taille minimale
                if os.path.getsize(filepath) < 500:
                    os.remove(filepath)
                    continue

                return relative

            except Exception:
                if os.path.exists(filepath):
                    os.remove(filepath)
                continue

        return None

    def _supprimer_photo(self, matricule):
        """Supprime le fichier et met photo à NULL"""
        try:
            emp = InformationPersonnelle.objects.get(numero_matricule=matricule)
            old_path = os.path.join(settings.MEDIA_ROOT, str(emp.photo))
            if os.path.exists(old_path):
                os.remove(old_path)
            emp.photo = None
            emp.save(update_fields=['photo'])
        except Exception:
            pass
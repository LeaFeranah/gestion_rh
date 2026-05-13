# personnel/management/commands/convert_bmp_to_jpg.py

import os
import sys
from PIL import Image, ImageFile
from django.core.management.base import BaseCommand
from django.conf import settings
from personnel.models import InformationPersonnelle

ImageFile.LOAD_TRUNCATED_IMAGES = True

class Command(BaseCommand):
    help = 'Convertit les photos BMP en JPG et supprime les corrompus'

    def handle(self, *args, **kwargs):
        employes = list(InformationPersonnelle.objects.filter(photo__endswith='.bmp'))
        total = len(employes)
        print(f"🔍 {total} photos BMP trouvées", flush=True)

        success = 0
        deleted = 0

        for emp in employes:
            old_path = os.path.join(settings.MEDIA_ROOT, str(emp.photo))

            # Fichier inexistant
            if not os.path.exists(old_path):
                print(f"⚠️  {emp.numero_matricule} - fichier manquant", flush=True)
                emp.photo = None
                emp.save(update_fields=['photo'])
                deleted += 1
                continue

            # Tenter la conversion
            try:
                new_relative = str(emp.photo).replace('.bmp', '.jpg')
                new_path = os.path.join(settings.MEDIA_ROOT, new_relative)

                with Image.open(old_path) as img:
                    img.convert('RGB').save(new_path, 'JPEG', quality=85)

                os.remove(old_path)
                emp.photo = new_relative
                emp.save(update_fields=['photo'])
                success += 1
                print(f"✅ {emp.numero_matricule}", flush=True)

            except Exception as e:
                # Afficher l'erreur exacte
                print(f"❌ {emp.numero_matricule} | {type(e).__name__}: {e}", flush=True)

                # Supprimer le BMP corrompu et vider la photo
                try:
                    if os.path.exists(old_path):
                        os.remove(old_path)
                    emp.photo = None
                    emp.save(update_fields=['photo'])
                    deleted += 1
                    print(f"   🗑️  supprimé", flush=True)
                except Exception as e2:
                    print(f"   ⚠️  impossible de supprimer: {e2}", flush=True)

        print(f"\n{'='*50}", flush=True)
        print(f"✅ Convertis          : {success}", flush=True)
        print(f"🗑️  Supprimés          : {deleted}", flush=True)
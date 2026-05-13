# personnel/management/commands/verifier_photos.py

import os
from PIL import Image
from django.core.management.base import BaseCommand
from django.conf import settings
from personnel.models import InformationPersonnelle

class Command(BaseCommand):
    help = 'Vérifie les photos qui ne s\'affichent pas'

    def handle(self, *args, **kwargs):
        employes = InformationPersonnelle.objects.exclude(
            photo=None
        ).exclude(photo='')

        total = employes.count()
        print(f"🔍 {total} employés avec photo en DB\n", flush=True)

        fichier_manquant = []
        fichier_corrompu = []
        ok = 0

        for emp in employes:
            path = os.path.join(settings.MEDIA_ROOT, str(emp.photo))

            if not os.path.exists(path):
                fichier_manquant.append(emp.numero_matricule)
                continue

            try:
                with Image.open(path) as img:
                    img.verify()
                ok += 1
            except Exception as e:
                fichier_corrompu.append((emp.numero_matricule, str(e)))

        print(f"✅ Photos OK          : {ok}")
        print(f"❌ Fichiers manquants : {len(fichier_manquant)}")
        print(f"⚠️  Fichiers corrompus : {len(fichier_corrompu)}")

        if fichier_manquant:
            print(f"\n📋 Matricules manquants (premiers 10):")
            for m in fichier_manquant[:10]:
                print(f"   - {m}")

        if fichier_corrompu:
            print(f"\n📋 Fichiers corrompus (premiers 10):")
            for m, err in fichier_corrompu[:10]:
                print(f"   - {m} : {err}")
# presence/management/commands/generer_dates_annee.py
from django.core.management.base import BaseCommand
from presence.models import Date

class Command(BaseCommand):
    help = 'Génère les dates pour une année complète'

    def add_arguments(self, parser):
        parser.add_argument('annee', type=int, help='Année à générer (ex: 2024)')

    def handle(self, *args, **options):
        annee = options['annee']
        
        self.stdout.write(f"Génération des dates pour l'année {annee}...")
        
        total = 0
        for mois in range(1, 13):
            dates = Date.generer_dates_mois(annee, mois)
            total += len(dates)
            
            mois_fr = [
                'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
            ]
            self.stdout.write(f"  ✓ {mois_fr[mois-1]}: {len(dates)} dates")
        
        self.stdout.write(self.style.SUCCESS(f"\n✅ Total: {total} dates générées pour {annee}"))
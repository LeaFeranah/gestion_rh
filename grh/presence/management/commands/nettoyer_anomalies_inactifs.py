from django.core.management.base import BaseCommand
from django.db.models import Q

class Command(BaseCommand):
    help = "Supprime les anomalies des employés inactifs"

    def handle(self, *args, **kwargs):
        from personnel.models import InformationPersonnelle
        from presence.models import Anomalie, UserInfo

        # Badges des employés ACTIFS
        badges_actifs = set(
            InformationPersonnelle.objects.filter(
                Q(depart__isnull=True) | Q(depart='') | Q(depart='0')
            ).values_list('numero_matricule', flat=True)
        )

        # UserIDs actifs
        userids_actifs = set(
            UserInfo.objects.filter(
                badgenumber__in=badges_actifs
            ).values_list('userid', flat=True)
        )

        # Supprimer anomalies des inactifs
        deleted, _ = Anomalie.objects.exclude(
            userid__in=userids_actifs
        ).delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ {deleted} anomalies d'employés inactifs supprimées."
            )
        )
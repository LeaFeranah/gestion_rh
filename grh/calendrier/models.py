from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class Calendrier(models.Model):
    """
    Calendrier d'entreprise regroupant des événements et jours fériés.
    Chaque calendrier correspond à une année ou une période donnée.
    """
    titre = models.CharField(max_length=200, verbose_name="Titre du calendrier")
    annee = models.IntegerField(verbose_name="Année")
    description = models.TextField(null=True, blank=True, verbose_name="Description")
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='calendriers_crees',
        verbose_name="Créé par"
    )
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'calendrier'
        ordering = ['-annee', 'titre']
        unique_together = ('titre', 'annee')
        verbose_name = "Calendrier"
        verbose_name_plural = "Calendriers"

    def __str__(self):
        return f"{self.titre} ({self.annee})"


class JourFerie(models.Model):
    """
    Jour férié ou événement spécial rattaché à un calendrier.
    Supporte les jours récurrents (même date chaque année).
    """
    TYPE_CHOICES = [
        ('ferie_national', 'Férié national'),
        ('ferie_entreprise', 'Férié entreprise'),
        ('evenement', 'Événement'),
        ('fermeture', 'Fermeture'),
        ('autre', 'Autre'),
    ]

    COULEUR_CHOICES = [
        ('#ef4444', 'Rouge'),
        ('#f97316', 'Orange'),
        ('#eab308', 'Jaune'),
        ('#22c55e', 'Vert'),
        ('#3b82f6', 'Bleu'),
        ('#8b5cf6', 'Violet'),
        ('#ec4899', 'Rose'),
        ('#6b7280', 'Gris'),
        ('#56656b', 'Ardoise (AKJ)'),
        ('#0ea5e9', 'Cyan'),
    ]

    calendrier = models.ForeignKey(
        Calendrier,
        on_delete=models.CASCADE,
        related_name='jours_feries',
        verbose_name="Calendrier"
    )
    titre = models.CharField(max_length=200, verbose_name="Titre / Nom du jour")
    date = models.DateField(verbose_name="Date")
    type_jour = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES,
        default='ferie_national',
        verbose_name="Type"
    )
    couleur = models.CharField(
        max_length=10,
        choices=COULEUR_CHOICES,
        default='#ef4444',
        verbose_name="Couleur"
    )
    est_recurrent = models.BooleanField(
        default=False,
        verbose_name="Récurrent chaque année",
        help_text="Si coché, ce jour sera automatiquement considéré férié chaque année"
    )
    description = models.TextField(null=True, blank=True, verbose_name="Description / Note")
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='jours_feries_crees',
        verbose_name="Créé par"
    )
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'calendrier_jour_ferie'
        ordering = ['date']
        verbose_name = "Jour férié"
        verbose_name_plural = "Jours fériés"

    def __str__(self):
        return f"{self.titre} – {self.date}"

    def clean(self):
        if self.date and self.calendrier_id:
            # Vérifier que la date est dans l'année du calendrier
            try:
                cal = Calendrier.objects.get(pk=self.calendrier_id)
                if self.date.year != cal.annee:
                    raise ValidationError(
                        f"La date doit être dans l'année {cal.annee} du calendrier."
                    )
            except Calendrier.DoesNotExist:
                pass
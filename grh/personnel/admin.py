from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import InformationPersonnelle, DossierPersonnel

# Inline pour le dossier personnel
class DossierPersonnelInline(admin.StackedInline):
    model = DossierPersonnel
    extra = 0  # pas de formulaire supplémentaire vide
    max_num = 1  # un seul dossier par employé

# Admin de l'employé
@admin.register(InformationPersonnelle)
class InformationPersonnelleAdmin(admin.ModelAdmin):
    list_display = ('numero_matricule', 'nom_complet')
    inlines = [DossierPersonnelInline]  # on ajoute l'inline ici

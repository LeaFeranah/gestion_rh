from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import InformationPersonnelle, DossierPersonnel

# Inline pour le dossier personnel
class DossierPersonnelInline(admin.StackedInline):
    model = DossierPersonnel
    extra = 0  
    max_num = 1  

# Admin de l'employé
@admin.register(InformationPersonnelle)
class InformationPersonnelleAdmin(admin.ModelAdmin):
    list_display = ('numero_matricule', 'nom_complet')
    inlines = [DossierPersonnelInline]  

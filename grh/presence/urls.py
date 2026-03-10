from django.urls import path
from .views import *

urlpatterns = [
    # ===== GESTION DES DATES =====
    path('generer-dates/', DateGenerationAPIView.as_view(), name='generer-dates'),
    path('dates/', DateListAPIView.as_view(), name='date-list'),

    # ===== GESTION DES ÉVÉNEMENTS =====
    path('evenements/', EvenementListAPIView.as_view(), name='evenement-list'),
    path('evenements/<int:pk>/', EvenementDetailAPIView.as_view(), name='evenement-detail'),
    path('evenements/user/<int:userid>/date/<str:date_str>/', EvenementByUserDateAPIView.as_view(), name='evenement-user-date'),
    path('types-evenements/', TypesEvenementAPIView.as_view(), name='types-evenements'),
    
    # ===== GESTION DES HORAIRES DE SECTION =====
    path('horaires-section/', HoraireSectionListAPIView.as_view(), name='horaires-section-list'),
    path('horaires-section/<str:section>/', HoraireSectionDetailAPIView.as_view(), name='horaires-section-detail'),
    path('initialiser-horaires/', InitialiserHorairesAPIView.as_view(), name='initialiser-horaires'),
    
    # ===== PRÉSENCES AVEC CALCULS =====
    path('mois/calculee/', PresenceMoisCalculeeAPIView.as_view(), name='presence-mois-calculee'),
    path('mois/detail/calculee/', PresenceMoisDetailCalculeeAPIView.as_view(), name='presence-mois-detail-calculee'),
    
    # ===== PRÉSENCES SIMPLES =====
    path('mois/', PresenceMoisAPIView.as_view(), name='presence-mois'),
    path('mois/detail/', PresenceMoisDetailAPIView.as_view(), name='presence-mois-detail'),
    path('mois/recap/', PresenceMoisRecapAPIView.as_view(), name='presence-mois-recap'),
    path('', PresenceListAPIView.as_view(), name='presence-list'),
    path('badge/<str:badgenumber>/', PresenceAPIView.as_view(), name='presence-by-badge'),

      # ===== GESTION DES ANOMALIES =====
  
    path('anomalies/', AnomalieListAPIView.as_view(), name='anomalie-list'),
    path('anomalies/<int:pk>/', AnomalieDetailAPIView.as_view(), name='anomalie-detail'),
    path('anomalies/<int:pk>/corriger/', CorrigerAnomalieAPIView.as_view(), name='anomalie-corriger'),
    path('detecter-anomalies/', DetecterAnomaliesAPIView.as_view(), name='detecter-anomalies'),
    path('anomalies/par-section/', AnomalieParSectionAPIView.as_view(), name='anomalie-par-section'),
    path('anomalies-corrigees/', AnomaliesCorrigeesAPIView.as_view(), name='anomalies-corrigees'),

        # ===== MODIFICATION MANUELLE DES HEURES =====
    path('modifier-heures/', ModifierHeuresManuellementAPIView.as_view(), name='modifier-heures'),
    path('supprimer-heures/', SupprimerHeuresManuellementAPIView.as_view(), name='supprimer-heures'),
    path('heures-jour/', GetHeuresJourAPIView.as_view(), name='heures-jour'),




    # Ajouter dans urlpatterns
    path('sections/', SectionListAPIView.as_view(), name='section-list'),
    path('sections/<int:section_id>/employes/', SectionEmployesAPIView.as_view(), name='section-employes'),
]
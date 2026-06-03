from django.urls import path
from .views import (
    CalendrierListAPIView,
    CalendrierDetailAPIView,
    JourFerieListAPIView,
    JourFerieDetailAPIView,
    TousJoursFeriesAPIView,
)

urlpatterns = [
    # Calendriers
    path('', CalendrierListAPIView.as_view(), name='calendrier-list'),
    path('<int:pk>/', CalendrierDetailAPIView.as_view(), name='calendrier-detail'),

    # Jours fériés d'un calendrier
    path('<int:cal_pk>/jours/', JourFerieListAPIView.as_view(), name='jour-ferie-list'),

    # Détail / modif / suppression d'un jour
    path('jours/<int:pk>/', JourFerieDetailAPIView.as_view(), name='jour-ferie-detail'),

    # Vue globale
    path('tous-jours/', TousJoursFeriesAPIView.as_view(), name='tous-jours-feries'),
]
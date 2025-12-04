from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import *

router = DefaultRouter()
router.register(r'employes', InformationPersonnelleViewSet)
router.register(r'professionnelle', InformationProfessionnelleViewSet)
router.register(r'bancaire', InformationBancaireViewSet)
router.register(r'sociale', InformationSocialeViewSet)
router.register(r'dossier', DossierPersonnelViewSet)
router.register(r'familiale', InformationFamilialeViewSet)
router.register(r'enfants', EnfantViewSet)  
router.register(r'salaire', InformationSalairePersonnelViewSet)
router.register(r'historique-salaire', HistoriqueSalaireViewSet, basename='historique-salaire') 



urlpatterns = [
    path('', include(router.urls)),
    
    # Authentification
    path('login/', login_api, name='login'),
    path('logout/', logout_api, name='logout'),
    
    # Dashboard et profil
    path('mes-employes/', mes_employes, name='mes_employes'),
    path('mes-statistiques/', mes_statistiques, name='mes_statistiques'),
    path('profil/', profil_utilisateur, name='profil'),
 
]
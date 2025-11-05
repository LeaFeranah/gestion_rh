# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from .views import EmployeViewSet, DocumentViewSet

# router = DefaultRouter()
# router.register(r'employes', EmployeViewSet)
# router.register(r'documents', DocumentViewSet)

# urlpatterns = [
#     path('', include(router.urls)),
# ]


from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'employes', InformationPersonnelleViewSet)
#router.register(r'professionnelle', InformationProfessionnelleViewSet)
router.register(r'bancaire', InformationBancaireViewSet)
router.register(r'sociale', InformationSocialeViewSet)
#router.register(r'complementaire', InformationComplementaireViewSet)
router.register(r'dossier', DossierPersonnelViewSet)
router.register(r'familiale', InformationFamilialeViewSet)
router.register(r'enfants', EnfantViewSet)  
router.register(r'salaire', InformationSalairePersonnelViewSet)


urlpatterns = [
    path('', include(router.urls)),
]

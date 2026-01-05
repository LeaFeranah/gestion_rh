# from django.urls import path
# from .views import PresenceAPIView

# urlpatterns = [
#     path('<int:user_id>/', PresenceAPIView.as_view()),
# ]


from django.urls import path
from .views import *

urlpatterns = [
  
    # Routes pour gérer les dates
    path('generer-dates/', DateGenerationAPIView.as_view(), name='generer-dates'),
    path('dates/', DateListAPIView.as_view(), name='date-list'),
    
    # Routes pour les présences par mois
    path('mois/', PresenceMoisAPIView.as_view(), name='presence-mois'),
    path('mois/detail/', PresenceMoisDetailAPIView.as_view(), name='presence-mois-detail'),
    path('mois/recap/', PresenceMoisRecapAPIView.as_view(), name='presence-mois-recap'),
    path('', PresenceListAPIView.as_view(), name='presence-list'),
    #path('<str:badgenumber>/', PresenceAPIView.as_view(), name='presence-by-badge'),
    path('badge/<str:badgenumber>/', PresenceAPIView.as_view(), name='presence-by-badge'),
]
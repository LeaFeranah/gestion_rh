from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmployeViewSet, DocumentViewSet

router = DefaultRouter()
router.register(r'employes', EmployeViewSet)
router.register(r'documents', DocumentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

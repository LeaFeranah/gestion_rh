from rest_framework import viewsets
from .models import Employe, Document
from .serializers import EmployeSerializer, DocumentSerializer
from rest_framework.parsers import MultiPartParser, FormParser

# CRUD complet pour Employé
class EmployeViewSet(viewsets.ModelViewSet):
    queryset = Employe.objects.all().order_by('matricule')
    serializer_class = EmployeSerializer

# CRUD pour les documents (upload séparé)
class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    parser_classes = [MultiPartParser, FormParser]  # Pour upload fichiers

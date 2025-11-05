# from rest_framework import viewsets
# from .models import Employe, Document
# from .serializers import EmployeSerializer, DocumentSerializer
# from rest_framework.parsers import MultiPartParser, FormParser

# # CRUD complet pour Employé
# class EmployeViewSet(viewsets.ModelViewSet):
#     queryset = Employe.objects.all().order_by('matricule')
#     serializer_class = EmployeSerializer

# # CRUD pour les documents (upload séparé)
# class DocumentViewSet(viewsets.ModelViewSet):
#     queryset = Document.objects.all()
#     serializer_class = DocumentSerializer
#     parser_classes = [MultiPartParser, FormParser]  # Pour upload fichiers


# from rest_framework import viewsets
# from .models import *
# from .serializers import *

# class InformationPersonnelleViewSet(viewsets.ModelViewSet):
#     queryset = InformationPersonnelle.objects.all()
#     serializer_class = InformationPersonnelleSerializer

# class InformationProfessionnelleViewSet(viewsets.ModelViewSet):
#     queryset = InformationProfessionnelle.objects.all()
#     serializer_class = InformationProfessionnelleSerializer

# class InformationBancaireViewSet(viewsets.ModelViewSet):
#     queryset = InformationBancaire.objects.all()
#     serializer_class = InformationBancaireSerializer

# class InformationSocialeViewSet(viewsets.ModelViewSet):
#     queryset = InformationSociale.objects.all()
#     serializer_class = InformationSocialeSerializer

# class InformationComplementaireViewSet(viewsets.ModelViewSet):
#     queryset = InformationComplementaire.objects.all()
#     serializer_class = InformationComplementaireSerializer


from rest_framework import viewsets
from .models import *
from .serializers import *

class DossierPersonnelViewSet(viewsets.ModelViewSet):
    queryset = DossierPersonnel.objects.all()
    serializer_class = DossierPersonnelSerializer
    
class InformationPersonnelleViewSet(viewsets.ModelViewSet):
    queryset = InformationPersonnelle.objects.all()
    
    # Choisir serializer selon l’action
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return InformationPersonnellePUTSerializer
        return InformationPersonnelleSerializer


# class InformationProfessionnelleViewSet(viewsets.ModelViewSet):
#     queryset = InformationProfessionnelle.objects.all()
#     serializer_class = InformationProfessionnelleSerializer

class InformationBancaireViewSet(viewsets.ModelViewSet):
    queryset = InformationBancaire.objects.all()
    serializer_class = InformationBancaireSerializer

class InformationSocialeViewSet(viewsets.ModelViewSet):
    queryset = InformationSociale.objects.all()
    serializer_class = InformationSocialeSerializer

# class InformationComplementaireViewSet(viewsets.ModelViewSet):
#     queryset = InformationComplementaire.objects.all()
#     serializer_class = InformationComplementaireSerializer


# ✅ Nouveau : Informations Familiales
class InformationFamilialeViewSet(viewsets.ModelViewSet):
    queryset = InformationFamiliale.objects.all()
    serializer_class = InformationFamilialeSerializer


# ✅ Nouveau : Enfants
class EnfantViewSet(viewsets.ModelViewSet):
    queryset = Enfant.objects.all()
    serializer_class = EnfantSerializer

class InformationSalairePersonnelViewSet(viewsets.ModelViewSet):
    queryset = InformationSalairePersonnel.objects.all()
    serializer_class = InformationSalairePersonnelSerializer

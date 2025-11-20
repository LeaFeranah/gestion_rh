# from rest_framework import viewsets
# from rest_framework import viewsets, status
# from rest_framework.decorators import api_view, permission_classes, action
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated, AllowAny
# from rest_framework.authentication import SessionAuthentication, TokenAuthentication
# from django.contrib.auth import login, logout, authenticate
# from .models import *
# from .serializers import *



# class BaseEmployeViewSet(viewsets.ModelViewSet):
#     """
#     ViewSet de base avec authentification et filtrage par utilisateur
#     """
#     authentication_classes = [SessionAuthentication, TokenAuthentication]
#     permission_classes = [IsAuthenticated]
    
#     def get_queryset(self):
#         # Chaque RH ne voit que les employés qu'elle a créés
#         return self.queryset.filter(created_by=self.request.user)
    
#     def perform_create(self, serializer):
#         # Automatiquement assigner l'utilisateur connecté comme créateur
#         serializer.save(created_by=self.request.user)

# class DossierPersonnelViewSet(viewsets.ModelViewSet):
#     queryset = DossierPersonnel.objects.all()
#     serializer_class = DossierPersonnelSerializer
    
# class InformationPersonnelleViewSet(viewsets.ModelViewSet):
#     queryset = InformationPersonnelle.objects.all()
    
#     # Choisir serializer selon l’action
#     def get_serializer_class(self):
#         if self.action in ['update', 'partial_update']:
#             return InformationPersonnellePUTSerializer
#         return InformationPersonnelleSerializer

# class InformationBancaireViewSet(viewsets.ModelViewSet):
#     queryset = InformationBancaire.objects.all()
#     serializer_class = InformationBancaireSerializer

# class InformationSocialeViewSet(viewsets.ModelViewSet):
#     queryset = InformationSociale.objects.all()
#     serializer_class = InformationSocialeSerializer


# # ✅ Nouveau : Informations Familiales
# class InformationFamilialeViewSet(viewsets.ModelViewSet):
#     queryset = InformationFamiliale.objects.all()
#     serializer_class = InformationFamilialeSerializer


# # ✅ Nouveau : Enfants
# class EnfantViewSet(viewsets.ModelViewSet):
#     queryset = Enfant.objects.all()
#     serializer_class = EnfantSerializer

# class InformationSalairePersonnelViewSet(viewsets.ModelViewSet):
#     queryset = InformationSalairePersonnel.objects.all()
#     serializer_class = InformationSalairePersonnelSerializer


# # 🔹 Statistiques pour le dashboard RH
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def mes_statistiques(request):
#     """Retourne les statistiques des employés du RH connecté"""
#     user = request.user
#     employes = InformationPersonnelle.objects.filter(created_by=user)
    
#     total_employes = employes.count()
#     hommes = employes.filter(sexe='Masculin').count()
#     femmes = employes.filter(sexe='Féminin').count()
#     a_la_retraite = len([e for e in employes if e.retraite == "Oui"])
    
#     return Response({
#         'total_employes': total_employes,
#         'hommes': hommes,
#         'femmes': femmes,
#         'a_la_retraite': a_la_retraite,
#         'departement': user.get_departement_display()
#     })


from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from django.contrib.auth import login, logout, authenticate
from .models import *
from .serializers import *


# ========== ViewSets avec authentification et filtrage par utilisateur ==========

class DossierPersonnelViewSet(viewsets.ModelViewSet):
    queryset = DossierPersonnel.objects.all()
    serializer_class = DossierPersonnelSerializer
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Chaque RH ne voit que les dossiers des employés qu'elle a créés"""
        return DossierPersonnel.objects.filter(employe__created_by=self.request.user)


class InformationPersonnelleViewSet(viewsets.ModelViewSet):
    queryset = InformationPersonnelle.objects.all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Chaque RH ne voit que les employés qu'elle a créés"""
        return InformationPersonnelle.objects.filter(created_by=self.request.user)
    
    def get_serializer_class(self):
        """Choisir serializer selon l'action"""
        if self.action in ['update', 'partial_update']:
            return InformationPersonnellePUTSerializer
        return InformationPersonnelleSerializer
    
    def perform_create(self, serializer):
        """Automatiquement assigner l'utilisateur connecté comme créateur"""
        serializer.save(created_by=self.request.user)


class InformationBancaireViewSet(viewsets.ModelViewSet):
    queryset = InformationBancaire.objects.all()
    serializer_class = InformationBancaireSerializer
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrer par employés du RH connecté"""
        return InformationBancaire.objects.filter(employe__created_by=self.request.user)


class InformationSocialeViewSet(viewsets.ModelViewSet):
    queryset = InformationSociale.objects.all()
    serializer_class = InformationSocialeSerializer
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrer par employés du RH connecté"""
        return InformationSociale.objects.filter(employe__created_by=self.request.user)


class InformationFamilialeViewSet(viewsets.ModelViewSet):
    queryset = InformationFamiliale.objects.all()
    serializer_class = InformationFamilialeSerializer
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrer par employés du RH connecté"""
        return InformationFamiliale.objects.filter(employe__created_by=self.request.user)


class EnfantViewSet(viewsets.ModelViewSet):
    queryset = Enfant.objects.all()
    serializer_class = EnfantSerializer
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrer par enfants des employés du RH connecté"""
        return Enfant.objects.filter(familiale__employe__created_by=self.request.user)


class InformationSalairePersonnelViewSet(viewsets.ModelViewSet):
    queryset = InformationSalairePersonnel.objects.all()
    serializer_class = InformationSalairePersonnelSerializer
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrer par employés du RH connecté"""
        return InformationSalairePersonnel.objects.filter(employe__created_by=self.request.user)


# ========== API Views pour authentification et statistiques ==========

# @api_view(['POST'])
# @permission_classes([AllowAny])  # Permet l'accès sans authentification pour le login
# def login_api(request):
#     """
#     Connexion d'un utilisateur RH
#     POST: {"username": "rh1", "password": "motdepasse"}
#     Retourne: {"token": "abc123...", "username": "rh1", "message": "Connexion réussie"}
#     """
#     username = request.data.get('username')
#     password = request.data.get('password')
    
#     if not username or not password:
#         return Response(
#             {'error': 'Username et password requis'}, 
#             status=status.HTTP_400_BAD_REQUEST
#         )
    
#     user = authenticate(username=username, password=password)
    
#     if user is not None:
#         #login(request, user)
        
#         # Créer ou récupérer le token
#         from rest_framework.authtoken.models import Token
#         token, created = Token.objects.get_or_create(user=user)
        
#         return Response({
#             'message': 'Connexion réussie',
#             'token': token.key,
#             'username': user.username,
#             'email': user.email,
#         })
#     else:
#         return Response(
#             {'error': 'Identifiants incorrects'}, 
#             status=status.HTTP_401_UNAUTHORIZED
#         )


@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    """
    Connexion d'un utilisateur RH - Version corrigée
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(username=username, password=password)
    
    if user is not None:
        from rest_framework.authtoken.models import Token
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'message': 'Connexion réussie',
            'token': token.key,
            'username': user.username,
            'email': user.email,
        })
    else:
        return Response(
            {'error': 'Identifiants incorrects'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api(request):
    """
    Déconnexion d'un utilisateur RH
    Supprime le token de l'utilisateur
    """
    try:
        # Supprimer le token de l'utilisateur
        request.user.auth_token.delete()
    except:
        pass
    
    logout(request)
    return Response({'message': 'Déconnexion réussie'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mes_employes(request):
    """
    Retourne la liste des employés créés par le RH connecté
    """
    employes = InformationPersonnelle.objects.filter(created_by=request.user)
    data = []
    
    for e in employes:
        data.append({
            'id': e.id,
            'numero_matricule': e.numero_matricule,
            'nom': e.nom,
            'prenoms': e.prenoms,
            'sexe': e.sexe,
            'fonction': e.fonction,
            'age': e.age,
            'retraite': e.retraite,
        })
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mes_statistiques(request):
    """
    Retourne les statistiques des employés du RH connecté
    """
    user = request.user
    employes = InformationPersonnelle.objects.filter(created_by=user)
    
    total_employes = employes.count()
    hommes = employes.filter(sexe='Masculin').count()
    femmes = employes.filter(sexe='Féminin').count()
    a_la_retraite = len([e for e in employes if e.retraite == "Oui"])
    
    return Response({
        'total_employes': total_employes,
        'hommes': hommes,
        'femmes': femmes,
        'a_la_retraite': a_la_retraite,
        'username': user.username,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profil_utilisateur(request):
    """
    Retourne les informations du RH connecté
    """
    user = request.user
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_staff': user.is_staff,
    })
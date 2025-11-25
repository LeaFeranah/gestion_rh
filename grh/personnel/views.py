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
    
    def perform_create(self, serializer):
        """Créer un salaire et enregistrer l'historique"""
        salaire = serializer.save()
        
        # Créer l'historique de création
        HistoriqueSalaire.objects.create(
            employe=salaire.employe,
            action='CREATE',
            modifie_par=self.request.user,
            # Anciennes valeurs = None pour création
            ancienne_categorie=None,
            ancienne_indice=None,
            ancien_taux_horaire=None,
            ancien_salaire_base=None,
            ancienne_autre_indemnite=None,
            ancienne_prime_anciennete=None,
            ancienne_indemnite_deplacement=None,
            ancien_salaire_total=None,
            # Nouvelles valeurs = valeurs créées
            nouvelle_categorie=salaire.categorie,
            nouvelle_indice=salaire.indice,
            nouveau_taux_horaire=salaire.taux_horaire,
            nouveau_salaire_base=salaire.salaire_base,
            nouvelle_autre_indemnite=salaire.autre_indemnite,
            nouvelle_prime_anciennete=salaire.prime_anciennete,
            nouvelle_indemnite_deplacement=salaire.indemnite_deplacement,
            nouveau_salaire_total=salaire.salaire_total,
            commentaire="Création initiale du salaire"
        )
        
        print(f"✅ Historique de CRÉATION créé pour {salaire.employe.nom_complet}")
    
    def perform_update(self, serializer):
        """Mettre à jour un salaire et enregistrer l'historique"""
        # 🔥 IMPORTANT : Récupérer l'instance AVANT la modification
        instance = self.get_object()
        
        # Sauvegarder les ANCIENNES valeurs
        anciennes_valeurs = {
            'ancienne_categorie': instance.categorie,
            'ancienne_indice': instance.indice,
            'ancien_taux_horaire': instance.taux_horaire,
            'ancien_salaire_base': instance.salaire_base,
            'ancienne_autre_indemnite': instance.autre_indemnite,
            'ancienne_prime_anciennete': instance.prime_anciennete,
            'ancienne_indemnite_deplacement': instance.indemnite_deplacement,
            'ancien_salaire_total': instance.salaire_total,
        }
        
        print(f"📋 Anciennes valeurs capturées : {anciennes_valeurs}")
        
        # Maintenant on sauvegarde les nouvelles valeurs
        salaire = serializer.save()
        
        print(f"📝 Nouvelles valeurs : categorie={salaire.categorie}, salaire_base={salaire.salaire_base}")
        
        # Créer l'historique de modification avec TOUTES les valeurs
        historique = HistoriqueSalaire.objects.create(
            employe=salaire.employe,
            action='UPDATE',
            modifie_par=self.request.user,
            # Anciennes valeurs
            ancienne_categorie=anciennes_valeurs['ancienne_categorie'],
            ancienne_indice=anciennes_valeurs['ancienne_indice'],
            ancien_taux_horaire=anciennes_valeurs['ancien_taux_horaire'],
            ancien_salaire_base=anciennes_valeurs['ancien_salaire_base'],
            ancienne_autre_indemnite=anciennes_valeurs['ancienne_autre_indemnite'],
            ancienne_prime_anciennete=anciennes_valeurs['ancienne_prime_anciennete'],
            ancienne_indemnite_deplacement=anciennes_valeurs['ancienne_indemnite_deplacement'],
            ancien_salaire_total=anciennes_valeurs['ancien_salaire_total'],
            # Nouvelles valeurs
            nouvelle_categorie=salaire.categorie,
            nouvelle_indice=salaire.indice,
            nouveau_taux_horaire=salaire.taux_horaire,
            nouveau_salaire_base=salaire.salaire_base,
            nouvelle_autre_indemnite=salaire.autre_indemnite,
            nouvelle_prime_anciennete=salaire.prime_anciennete,
            nouvelle_indemnite_deplacement=salaire.indemnite_deplacement,
            nouveau_salaire_total=salaire.salaire_total,
            commentaire=f"Modification du salaire"
        )
        
        print(f"✅ Historique de MODIFICATION créé : ID={historique.id}")
    
    @action(detail=True, methods=['get'], url_path='historique')
    def historique(self, request, pk=None):
        """Récupérer TOUT l'historique d'un salaire spécifique"""
        salaire = self.get_object()
        
        # Récupérer TOUS les historiques de cet employé
        historiques = HistoriqueSalaire.objects.filter(
            employe=salaire.employe
        ).order_by('-created_at')  # Du plus récent au plus ancien
        
        print(f"📊 Nombre d'historiques trouvés : {historiques.count()}")
        
        serializer = HistoriqueSalaireSerializer(historiques, many=True)
        
        return Response({
            'count': historiques.count(),
            'employe': salaire.employe.nom_complet,
            'historiques': serializer.data
        })
 


class HistoriqueSalaireViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet en lecture seule pour l'historique des salaires"""
    queryset = HistoriqueSalaire.objects.all()
    serializer_class = HistoriqueSalaireSerializer
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrer par employés du RH connecté"""
        return HistoriqueSalaire.objects.filter(
            employe__created_by=self.request.user
        ).select_related('employe', 'modifie_par')
    
    @action(detail=False, methods=['get'])
    def par_employe(self, request):
        """Récupérer l'historique filtré par employé"""
        employe_id = request.query_params.get('employe_id')
        
        if not employe_id:
            return Response(
                {'error': 'employe_id est requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        historiques = self.get_queryset().filter(employe_id=employe_id)
        serializer = self.get_serializer(historiques, many=True)
        return Response(serializer.data)
    

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
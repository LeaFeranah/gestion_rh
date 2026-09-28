
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from .models import *
from .serializers import *


# ========== ViewSets avec authentification et filtrage par utilisateur ==========

class InformationProfessionnelleViewSet(viewsets.ModelViewSet):
    """ViewSet pour InformationProfessionnelle avec gestion des évolutions de poste"""
    queryset = InformationProfessionnelle.objects.all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    # def get_queryset(self):
    #     """Chaque RH ne voit que les informations professionnelles des employés qu'elle a créés"""
    #     return InformationProfessionnelle.objects.filter(employe__created_by=self.request.user)
    def get_queryset(self):
        return InformationProfessionnelle.objects.all()
    
    def get_serializer_class(self):
        """Choisir serializer selon l'action"""
        if self.action == 'create':
            return InformationProfessionnelleCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return InformationProfessionnelleUpdateSerializer
        else:
            return InformationProfessionnelleSerializer
    
    # def perform_create(self, serializer):
    #     """Vérifier que l'employé appartient bien au RH connecté"""
    #     employe = serializer.validated_data.get('employe')
    #     if employe.created_by != self.request.user:
    #         raise serializers.ValidationError(
    #             {"employe": "Vous ne pouvez pas créer d'informations professionnelles pour cet employé."}
    #         )
    #     serializer.save()
    def perform_create(self, serializer):
        # Supprimer la vérification created_by
        serializer.save()
    
    def perform_update(self, serializer):
        """Gérer la mise à jour avec validation des champs sensibles"""
        try:
            serializer.save()
        except ValueError as e:
            raise serializers.ValidationError(
                {"non_field_errors": [str(e)]}
            )
    
    @action(detail=True, methods=['post'], url_path='creer-evolution')
    def creer_evolution(self, request, pk=None):
        """Créer une évolution de poste pour cet employé"""
        info_pro = self.get_object()
        
        # Vérifier que l'employé appartient au RH connecté
        if info_pro.employe.created_by != request.user:
            return Response(
                # {'error': "Vous n'êtes pas autorisé à créer une évolution pour cet employé."},
                # status=status.HTTP_403_FORBIDDEN
            )
        
        # Préparer les données avec l'employé
        data = request.data.copy()
        data['employe'] = info_pro.employe.id
        
        # Utiliser le serializer EvolutionPoste
        serializer = EvolutionPosteSerializer(
            data=data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            evolution = serializer.save()
            return Response(
                EvolutionPosteSerializer(evolution).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], url_path='evolutions')
    def list_evolutions(self, request, pk=None):
        """Liste toutes les évolutions de poste pour cet employé"""
        info_pro = self.get_object()
        evolutions = EvolutionPoste.objects.filter(
            employe=info_pro.employe
        ).order_by('-date_evolution')
        
        serializer = EvolutionPosteSerializer(evolutions, many=True)
        
        return Response({
            # 'employe': info_pro.employe.nom_complet,
            # 'information_professionnelle_id': info_pro.id,
            # 'evolutions_count': evolutions.count(),
            # 'evolutions': serializer.data
        })


class EvolutionPosteViewSet(viewsets.ModelViewSet):
    """ViewSet pour gérer les évolutions de poste"""
    queryset = EvolutionPoste.objects.all()
    serializer_class = EvolutionPosteSerializer
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    # def get_queryset(self):
    #     """Filtrer par employés du RH connecté"""
    #     return EvolutionPoste.objects.filter(
    #         employe__created_by=self.request.user
    #     ).select_related('employe', 'modifie_par')
    def get_queryset(self):
        return EvolutionPoste.objects.all().select_related('employe', 'modifie_par')
    
    # def perform_create(self, serializer):
    #     """Vérifier que l'employé appartient bien au RH connecté"""
    #     employe = serializer.validated_data.get('employe')
        
    #     if employe.created_by != self.request.user:
    #         raise serializers.ValidationError(
    #             {"employe": "Vous ne pouvez pas créer d'évolution de poste pour cet employé."}
    #         )
        
    #     serializer.save()
    def perform_create(self, serializer):
        # Supprimer la vérification created_by
        serializer.save()
    
    @action(detail=True, methods=['post'], url_path='appliquer')
    def appliquer_evolution(self, request, pk=None):
        """Action pour appliquer une évolution de poste"""
        evolution = self.get_object()
        
        # Vérifier que l'évolution appartient à un employé du RH connecté
        # if evolution.employe.created_by != request.user:
        #     return Response(
        #         {'error': "Vous n'êtes pas autorisé à appliquer cette évolution."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        
        # Vérifier le statut
        if evolution.statut == 'REALISEE':
            return Response(
                {'error': "Cette évolution a déjà été appliquée."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Appliquer l'évolution
        if evolution.appliquer_evolution():
            return Response({
                'message': 'Évolution appliquée avec succès.',
                'statut': evolution.statut
            })
        else:
            return Response(
                {'error': "Impossible d'appliquer l'évolution."},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], url_path='changer-statut')
    def changer_statut(self, request, pk=None):
        """Changer le statut d'une évolution"""
        evolution = self.get_object()
        nouveau_statut = request.data.get('statut')
        
        # if evolution.employe.created_by != request.user:
        #     return Response(
        #         {'error': "Vous n'êtes pas autorisé à modifier cette évolution."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        
        if nouveau_statut not in [choice[0] for choice in EvolutionPoste.STATUT_CHOICES]:
            return Response(
                {'error': "Statut invalide."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        evolution.statut = nouveau_statut
        evolution.save()
        
        return Response({
            'message': f'Statut changé à {evolution.get_statut_display()}',
            'statut': evolution.statut,
            'statut_display': evolution.get_statut_display()
        })
    
    @action(detail=False, methods=['get'], url_path='par-employe/(?P<employe_id>[^/.]+)')
    def par_employe(self, request, employe_id=None):
        """Récupérer toutes les évolutions d'un employé spécifique"""
        try:
            employe = InformationPersonnelle.objects.get(
                id=employe_id
                # created_by=request.user
            )
            
            evolutions = EvolutionPoste.objects.filter(
                employe=employe
            ).order_by('-date_evolution')
            
            serializer = self.get_serializer(evolutions, many=True)
            
            return Response({
                'employe': employe.nom_complet,
                'count': evolutions.count(),
                'evolutions': serializer.data
            })
        except InformationPersonnelle.DoesNotExist:
            return Response(
                {'error': "Employé non trouvé ou non autorisé."},
                status=status.HTTP_404_NOT_FOUND
            )




class InformationPersonnelleViewSet(viewsets.ModelViewSet):
    queryset = InformationPersonnelle.objects.none()  # pour DRF basename
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    # def get_queryset(self):
    #     if self.action == 'list':
    #         return InformationPersonnelle.objects.filter(
    #             created_by=self.request.user
    #         ).select_related('information_professionnelle').only(
    #             'id', 'numero_matricule', 'nom_complet', 'sexe',
    #             'appellation', 'photo', 'depart',
    #             # Champs du related nécessaires au serializer léger
    #             'information_professionnelle__fonction',
    #             'information_professionnelle__section',
    #             'information_professionnelle__responsable_section',
    #         )
        
    #     return InformationPersonnelle.objects.filter(
    #         created_by=self.request.user
    #     ).select_related(
    #         'information_professionnelle',
    #         'bancaire',
    #         'sociale',
    #         'salaire_personnel',
    #         'familiale',
    #     ).prefetch_related(
    #         'evolutions_poste',
    #         'familiale__enfants',
    #     )
    def get_queryset(self):
        if self.action == 'list':
            return InformationPersonnelle.objects.all().select_related(
                'information_professionnelle'
            ).only(
                'id', 'numero_matricule', 'nom_complet', 'sexe',
                'appellation', 'photo', 'depart',
                'information_professionnelle__fonction',
                'information_professionnelle__section',
                'information_professionnelle__responsable_section',
            )
        return InformationPersonnelle.objects.all().select_related(
            'information_professionnelle', 'bancaire',
            'sociale', 'salaire_personnel', 'familiale',
        ).prefetch_related('evolutions_poste', 'familiale__enfants')

    def get_serializer_class(self):
        if self.action == 'list':
            return InformationPersonnelleLightSerializer
        elif self.action in ['update', 'partial_update']:
            return InformationPersonnellePUTSerializer
        return InformationPersonnelleSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='creer-professionnelle')
    # def creer_information_professionnelle(self, request, pk=None):
    #     employe = self.get_object()
        
    #     if employe.created_by != request.user:
    #         return Response(
    #             {'error': "Vous n'êtes pas autorisé à créer l'information professionnelle pour cet employé."},
    #             status=status.HTTP_403_FORBIDDEN
    #         )
        
    #     if hasattr(employe, 'information_professionnelle'):
    #         return Response(
    #             {'error': "Une information professionnelle existe déjà pour cet employé."},
    #             status=status.HTTP_400_BAD_REQUEST
    #         )
        
    #     data = request.data.copy()
    #     data['employe'] = employe.id
        
    #     serializer = InformationProfessionnelleCreateSerializer(
    #         data=data,
    #         context={'request': request}
    #     )
        
    #     if serializer.is_valid():
    #         info_pro = serializer.save()
    #         return Response(
    #             InformationProfessionnelleSerializer(info_pro).data,
    #             status=status.HTTP_201_CREATED
    #         )
        
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def creer_information_professionnelle(self, request, pk=None):
        employe = self.get_object()

        if hasattr(employe, 'information_professionnelle'):
            return Response(
                {'error': "Une information professionnelle existe déjà pour cet employé."},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = request.data.copy()
        data['employe'] = employe.id

        serializer = InformationProfessionnelleCreateSerializer(
            data=data, context={'request': request}
        )

        if serializer.is_valid():
            info_pro = serializer.save()
            return Response(
                InformationProfessionnelleSerializer(info_pro).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





class DossierPersonnelViewSet(viewsets.ModelViewSet):
    queryset = DossierPersonnel.objects.all()
    serializer_class = DossierPersonnelSerializer
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    # def get_queryset(self):
    #     """Chaque RH ne voit que les dossiers des employés qu'elle a créés"""
    #     return DossierPersonnel.objects.filter(employe__created_by=self.request.user)
    def get_queryset(self):
        return DossierPersonnel.objects.all()


class InformationBancaireViewSet(viewsets.ModelViewSet):
    queryset = InformationBancaire.objects.all()
    serializer_class = InformationBancaireSerializer
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    # def get_queryset(self):
    #     """Filtrer par employés du RH connecté"""
    #     return InformationBancaire.objects.filter(employe__created_by=self.request.user)
    def get_queryset(self):
        return InformationBancaire.objects.all()


class InformationSocialeViewSet(viewsets.ModelViewSet):
    queryset = InformationSociale.objects.all()
    serializer_class = InformationSocialeSerializer
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    # def get_queryset(self):
    #     """Filtrer par employés du RH connecté"""
    #     return InformationSociale.objects.filter(employe__created_by=self.request.user)
    def get_queryset(self):
        return InformationSociale.objects.all()


class InformationFamilialeViewSet(viewsets.ModelViewSet):
    queryset = InformationFamiliale.objects.all()
    serializer_class = InformationFamilialeSerializer
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    # def get_queryset(self):
    #     """Filtrer par employés du RH connecté"""
    #     return InformationFamiliale.objects.filter(employe__created_by=self.request.user)
    def get_queryset(self):
        return InformationFamiliale.objects.all()


class EnfantViewSet(viewsets.ModelViewSet):
    queryset = Enfant.objects.all()
    serializer_class = EnfantSerializer
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    # def get_queryset(self):
    #     """Filtrer par enfants des employés du RH connecté"""
    #     return Enfant.objects.filter(familiale__employe__created_by=self.request.user)
    def get_queryset(self):
        return Enfant.objects.all()


class InformationSalairePersonnelViewSet(viewsets.ModelViewSet):
    queryset = InformationSalairePersonnel.objects.all()
    serializer_class = InformationSalairePersonnelSerializer
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    # def get_queryset(self):
    #     """Filtrer par employés du RH connecté"""
    #     return InformationSalairePersonnel.objects.filter(employe__created_by=self.request.user)
    def get_queryset(self):
        return InformationSalairePersonnel.objects.all()
    
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
    
    def perform_update(self, serializer):
        """Mettre à jour un salaire et enregistrer l'historique"""
        # Récupérer l'instance AVANT la modification
        instance = self.get_object()
        
        # Sauvegarder les ANCIENNES valeurs
        anciennes_valeurs = {
            'ancienne_categorie' : instance.categorie,
            'ancienne_indice': instance.indice,
            'ancien_taux_horaire': instance.taux_horaire,
            'ancien_salaire_base': instance.salaire_base,
            'ancienne_autre_indemnite': instance.autre_indemnite,
            'ancienne_prime_anciennete': instance.prime_anciennete,
            'ancienne_indemnite_deplacement': instance.indemnite_deplacement,
            'ancien_salaire_total': instance.salaire_total,
        }
        
        # Maintenant on sauvegarde les nouvelles valeurs
        salaire = serializer.save()
        
        # Créer l'historique de modification avec TOUTES les valeurs
        HistoriqueSalaire.objects.create(
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
    
    @action(detail=True, methods=['get'], url_path='historique')
    def historique(self, request, pk=None):
        """Récupérer TOUT l'historique d'un salaire spécifique"""
        salaire = self.get_object()
        
        # Récupérer TOUS les historiques de cet employé
        historiques = HistoriqueSalaire.objects.filter(
            employe=salaire.employe
        ).order_by('-created_at')
        
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
    
    # def get_queryset(self):
    #     """Filtrer par employés du RH connecté"""
    #     return HistoriqueSalaire.objects.filter(
    #         employe__created_by=self.request.user
    #     ).select_related('employe', 'modifie_par')
    def get_queryset(self):
        return HistoriqueSalaire.objects.all().select_related('employe', 'modifie_par')
    
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


# ========== API Views ==========

@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    """Connexion d'un utilisateur RH"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    
    user = authenticate(username=username, password=password)
    
    # if user is not None:
    #     from rest_framework.authtoken.models import Token
    #     token, created = Token.objects.get_or_create(user=user)
        
    #     return Response({
    #         'message': 'Connexion réussie',
    #         'token': token.key,
    #         'username': user.username,
    #         'email': user.email,
    #         'is_admin': user.is_staff,   
    #     })
    if user is not None:
        from rest_framework.authtoken.models import Token
        token, created = Token.objects.get_or_create(user=user)

        profil = getattr(user, 'profil', None)
        role = profil.role if profil else ('SUPERADMIN' if user.is_superuser else 'ADMIN')
        sections = list(profil.sections.values_list('nom_section', flat=True)) if profil else []

        return Response({
            'message': 'Connexion réussie',
            'token': token.key,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_staff,
            'role': role,
            'sections': sections,
        })
    else:
        return Response(
            {'error': 'Identifiants incorrects'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication, SessionAuthentication])  # ← ajoute ça
def modifier_utilisateur(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'Utilisateur non trouvé'}, status=status.HTTP_404_NOT_FOUND)

    username = request.data.get('username')
    password = request.data.get('password')

    if username:
        user.username = username
    if password:
        user.set_password(password)

    user.save()
    return Response({'message': 'Utilisateur mis à jour avec succès', 'username': user.username})




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api(request):
    """Déconnexion d'un utilisateur RH"""
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
    """Retourne la liste des employés créés par le RH connecté"""
    #employes = InformationPersonnelle.objects.filter(created_by=request.user)
    employes = InformationPersonnelle.objects.all()
    data = []
    
    for e in employes:
        data.append({
            'id': e.id,
            'numero_matricule': e.numero_matricule,
            'nom_complet': e.nom_complet,
            'sexe': e.sexe,
            'fonction': e.information_professionnelle.fonction if hasattr(e, 'information_professionnelle') else None,
            'section': e.information_professionnelle.section if hasattr(e, 'information_professionnelle') else None,
            'age': e.age,
            'retraite': e.retraite,
        })
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mes_statistiques(request):
    """Retourne les statistiques des employés du RH connecté"""
    user = request.user
    # employes = InformationPersonnelle.objects.filter(created_by=user)
    employes = InformationPersonnelle.objects.all()
    
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
    """Retourne les informations du RH connecté"""
    user = request.user
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_staff': user.is_staff,
    })

from django.contrib.auth.models import User
from .models import ProfilUtilisateur
from .serializers import UtilisateurSerializer
from .permissions import IsSuperAdmin
from rest_framework.views import APIView



def _sync_horaire_responsable(section_ids):
    """
    Recalcule le champ texte HoraireSection.responsable pour les sections
    données, à partir des comptes RESPONSABLE réellement liés à chaque section.
    """
    from presence.models import Section, HoraireSection
    for section_id in section_ids:
        try:
            section_obj = Section.objects.get(pk=section_id)
        except Section.DoesNotExist:
            continue
        usernames = list(
            section_obj.responsables.filter(role='RESPONSABLE')
            .values_list('user__username', flat=True)
        )
        HoraireSection.objects.filter(section=section_obj.nom_section).update(
            responsable=", ".join(usernames)
        )


class UtilisateurListCreateAPIView(APIView):
    """
    GET  /api/personnel/utilisateurs-admin/   → liste tous les comptes + rôle + section
    POST /api/personnel/utilisateurs-admin/   → crée un compte + son profil
    """
    permission_classes = [IsSuperAdmin]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get(self, request):
        users = User.objects.all().select_related('profil').prefetch_related('profil__sections').order_by('username')
        return Response(UtilisateurSerializer(users, many=True).data)

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        role = request.data.get('role', 'ADMIN')
        section_ids = request.data.get('sections', [])

        if not username or not password:
            return Response(
                {'error': "'username' et 'password' sont obligatoires"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if role not in dict(ProfilUtilisateur.ROLE_CHOICES):
            return Response({'error': f"role invalide: {role}"}, status=400)
        if role == 'RESPONSABLE' and not section_ids:
            return Response(
                {'error': "au moins une section est obligatoire quand role = RESPONSABLE"},
                status=400
            )
        if User.objects.filter(username=username).exists():
            return Response({'error': "Ce nom d'utilisateur existe déjà"}, status=400)

        user = User.objects.create_user(username=username, password=password)
        profil = ProfilUtilisateur.objects.create(user=user, role=role)
        if role == 'RESPONSABLE':
            profil.sections.set(section_ids)
            _sync_horaire_responsable(section_ids)
        return Response(UtilisateurSerializer(user).data, status=status.HTTP_201_CREATED)

    
class UtilisateurDetailAPIView(APIView):
    """
    PATCH  /api/personnel/utilisateurs-admin/{id}/   → modifie rôle/section/mot de passe
    DELETE /api/personnel/utilisateurs-admin/{id}/   → désactive le compte
    """
    permission_classes = [IsSuperAdmin]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            return None

    def patch(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return Response({'error': 'Utilisateur non trouvé'}, status=404)

        username = request.data.get('username')
        role = request.data.get('role')
        section_ids = request.data.get('sections')
        password = request.data.get('password')
        is_active = request.data.get('is_active')

        if username and username != user.username:
            if User.objects.exclude(pk=user.pk).filter(username=username).exists():
                return Response({'error': "Ce nom d'utilisateur existe déjà"}, status=400)
            user.username = username
            user.save()

        if password:
            user.set_password(password)
            user.save()

        if is_active is not None:
            user.is_active = bool(is_active)
            user.save()

        if role is not None:
            if role not in dict(ProfilUtilisateur.ROLE_CHOICES):
                return Response({'error': f"role invalide: {role}"}, status=400)
            if role == 'RESPONSABLE' and not section_ids:
                return Response(
                    {'error': "au moins une section est obligatoire quand role = RESPONSABLE"},
                    status=400
                )
            profil, _ = ProfilUtilisateur.objects.get_or_create(user=user)
            anciennes_sections = list(profil.sections.values_list('id', flat=True))
            profil.role = role
            if role == 'RESPONSABLE':
                profil.sections.set(section_ids or [])
            else:
                profil.sections.clear()
            profil.save()
            _sync_horaire_responsable(set(anciennes_sections) | set(section_ids or []))
        elif section_ids is not None:
            profil, _ = ProfilUtilisateur.objects.get_or_create(user=user)
            anciennes_sections = list(profil.sections.values_list('id', flat=True))
            profil.sections.set(section_ids)
            _sync_horaire_responsable(set(anciennes_sections) | set(section_ids))

        return Response(UtilisateurSerializer(user).data)

    def delete(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return Response({'error': 'Utilisateur non trouvé'}, status=404)
        username = user.username
        profil = getattr(user, 'profil', None)
        anciennes_sections = list(profil.sections.values_list('id', flat=True)) if profil else []
        user.delete()
        _sync_horaire_responsable(anciennes_sections)
        return Response({'message': f"Compte « {username} » supprimé définitivement"})
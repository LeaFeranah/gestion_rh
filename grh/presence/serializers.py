from rest_framework import serializers
from decimal import Decimal
from .models import Date, HoraireSection, Evenement, AnomaliePointage


class DateSerializer(serializers.ModelSerializer):
    code_affichage = serializers.ReadOnlyField()
    
    class Meta:
        model = Date
        fields = ['date', 'code_date', 'code_affichage', 'hors_periode', 'mois_reference']


class HoraireSectionSerializer(serializers.ModelSerializer):
    heure_entree_normale = serializers.ReadOnlyField()
    heure_sortie_normale = serializers.ReadOnlyField()
    sortie_samedi_normale = serializers.ReadOnlyField()
    sortie_vendredi_paiement_normale = serializers.ReadOnlyField()
    sortie_samedi_paiement_normale = serializers.ReadOnlyField()
    
    class Meta:
        model = HoraireSection
        fields = [
            'section', 
            'heure_entree', 
            'heure_sortie', 
            'sortie_samedi',
            'sortie_vendredi_paiement',
            'sortie_samedi_paiement',
            'heure_entree_normale',
            'heure_sortie_normale',
            'sortie_samedi_normale',
            'sortie_vendredi_paiement_normale',
            'sortie_samedi_paiement_normale'
        ]
    
    # Ajouter les validateurs pour les nouveaux champs
    def validate_sortie_vendredi_paiement(self, value):
        """Valide que l'heure de sortie vendredi paiement est entre 0 et 24"""
        try:
            if isinstance(value, str):
                value = Decimal(value)
            if not (0 <= float(value) < 24):
                raise serializers.ValidationError("L'heure de sortie vendredi paiement doit être entre 0 et 24")
            return value
        except (ValueError, TypeError):
            raise serializers.ValidationError("Format d'heure invalide")
    
    def validate_sortie_samedi_paiement(self, value):
        """Valide que l'heure de sortie samedi paiement est entre 0 et 24"""
        try:
            if isinstance(value, str):
                value = Decimal(value)
            if not (0 <= float(value) < 24):
                raise serializers.ValidationError("L'heure de sortie samedi paiement doit être entre 0 et 24")
            return value
        except (ValueError, TypeError):
            raise serializers.ValidationError("Format d'heure invalide")
        

class EvenementSerializer(serializers.ModelSerializer):
    type_evenement_display = serializers.CharField(source='get_type_evenement_display', read_only=True)
    user_name = serializers.SerializerMethodField()
    badgenumber = serializers.SerializerMethodField()
    
    class Meta:
        model = Evenement
        fields = [
            'id',
            'userid',
            'user_name',
            'badgenumber',
            'date',
            'type_evenement',
            'type_evenement_display',
            'commentaire',
            'cree_le',
            'modifie_le'
        ]
        read_only_fields = ['id', 'cree_le', 'modifie_le']
    
    def get_user_name(self, obj):
        """Récupère le nom de l'utilisateur"""
        try:
            from .models import UserInfo
            user = UserInfo.objects.get(userid=obj.userid)
            return user.name if user else f"User {obj.userid}"
        except:
            return f"User {obj.userid}"
    
    def get_badgenumber(self, obj):
        """Récupère le badgenumber"""
        try:
            from .models import UserInfo
            user = UserInfo.objects.get(userid=obj.userid)
            return user.badgenumber if user else None
        except:
            return None
    
    def validate_type_evenement(self, value):
        """Valide que le type d'événement est valide"""
        valid_types = [choice[0] for choice in Evenement.TYPES_EVENEMENT]
        if value not in valid_types:
            raise serializers.ValidationError(f"Type d'événement invalide. Choix: {', '.join(valid_types)}")
        return value
    

class AnomaliePointageSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    badgenumber = serializers.SerializerMethodField()
    
    class Meta:
        model = AnomaliePointage
        fields = [
            'id',
            'userid',
            'user_name',
            'badgenumber',
            'date',
            'heure_entree_modifiee',
            'heure_sortie_modifiee',
            'motif',
            'modifie_par',
            'cree_le',
            'modifie_le'
        ]
        read_only_fields = ['id', 'cree_le', 'modifie_le']
    
    def get_user_name(self, obj):
        """Récupère le nom de l'utilisateur"""
        try:
            from .models import UserInfo
            user = UserInfo.objects.get(userid=obj.userid)
            return user.name if user else f"User {obj.userid}"
        except:
            return f"User {obj.userid}"
    
    def get_badgenumber(self, obj):
        """Récupère le badgenumber"""
        try:
            from .models import UserInfo
            user = UserInfo.objects.get(userid=obj.userid)
            return user.badgenumber if user else None
        except:
            return None
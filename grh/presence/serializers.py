from rest_framework import serializers
from .models import Date, HoraireSection
from .models import Evenement

class DateSerializer(serializers.ModelSerializer):
    code_affichage = serializers.ReadOnlyField()
    
    class Meta:
        model = Date
        fields = ['date', 'code_date', 'code_affichage', 'hors_periode', 'mois_reference']


class HoraireSectionSerializer(serializers.ModelSerializer):
    heure_entree_normale = serializers.ReadOnlyField()
    heure_sortie_normale = serializers.ReadOnlyField()
    sortie_samedi_normale = serializers.ReadOnlyField()
    
    class Meta:
        model = HoraireSection
        fields = [
            'section', 
            'heure_entree', 
            'heure_sortie', 
            'sortie_samedi',
            'heure_entree_normale',
            'heure_sortie_normale',
            'sortie_samedi_normale'
        ]
    
    def validate_heure_entree(self, value):
        """Valide que l'heure d'entrée est entre 0 et 24"""
        if not (0 <= value < 24):
            raise serializers.ValidationError("L'heure d'entrée doit être entre 0 et 24")
        return value
    
    def validate_heure_sortie(self, value):
        """Valide que l'heure de sortie est entre 0 et 24"""
        if not (0 <= value < 24):
            raise serializers.ValidationError("L'heure de sortie doit être entre 0 et 24")
        return value
    
    def validate_sortie_samedi(self, value):
        """Valide que l'heure de sortie samedi est entre 0 et 24"""
        if not (0 <= value < 24):
            raise serializers.ValidationError("L'heure de sortie samedi doit être entre 0 et 24")
        return value
    
    
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
        user = obj.user
        return user.name if user else f"User {obj.userid}"
    
    def get_badgenumber(self, obj):
        """Récupère le badgenumber"""
        user = obj.user
        return user.badgenumber if user else None
    
    def validate_type_evenement(self, value):
        """Valide que le type d'événement est valide"""
        valid_types = [choice[0] for choice in Evenement.TYPES_EVENEMENT]
        if value not in valid_types:
            raise serializers.ValidationError(f"Type d'événement invalide. Choix: {', '.join(valid_types)}")
        return value
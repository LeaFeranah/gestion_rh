
from rest_framework import serializers
from decimal import Decimal
from .models import Date, HoraireSection, Evenement, Anomalie


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
    











# class AnomalieSerializer(serializers.ModelSerializer):
#     etat_display = serializers.CharField(source='get_etat_display', read_only=True)
#     user_name = serializers.SerializerMethodField()
#     badgenumber = serializers.SerializerMethodField()
    
#     # Codes pour affichage
#     code_date_reel = serializers.SerializerMethodField()
#     code_date_p = serializers.SerializerMethodField()
#     code_date_b = serializers.SerializerMethodField()
    
#     class Meta:
#         model = Anomalie
#         fields = [
#             'id',
#             'userid',
#             'user_name',
#             'badgenumber',
#             'section',
#             'date',
#             'checktype',
#             'code_date',
#             'code_date_reel',
#             'code_date_p',
#             'code_date_b',
#             'heure_brute_entree',
#             'heure_brute_sortie',
#             'heure_reelle_entree',
#             'heure_reelle_sortie',
#             'heure_comptabilisee_entree',
#             'heure_comptabilisee_sortie',
#             'etat',
#             'etat_display',
#             'corrigee',
#             'commentaire',
#             'cree_le',
#             'modifie_le'
#         ]
#         read_only_fields = ['id', 'cree_le', 'modifie_le', 'heure_brute_entree', 'heure_brute_sortie']
    
#     def get_user_name(self, obj):
#         """Récupère le nom de l'utilisateur"""
#         try:
#             from .models import UserInfo
#             user = UserInfo.objects.get(userid=obj.userid)
#             return user.name if user else f"User {obj.userid}"
#         except:
#             return f"User {obj.userid}"
    
#     def get_badgenumber(self, obj):
#         """Récupère le badgenumber"""
#         try:
#             from .models import UserInfo
#             user = UserInfo.objects.get(userid=obj.userid)
#             return user.badgenumber if user else None
#         except:
#             return None
    
#     def get_code_date_reel(self, obj):
#         """Code date avec heures réelles"""
#         return obj.code_date if obj.code_date else ''
    
#     def get_code_date_p(self, obj):
#         """Code date avec heures comptabilisées"""
#         return f"{obj.code_date}P" if obj.code_date else ''
    
#     def get_code_date_b(self, obj):
#         """Code date avec heures brutes"""
#         return f"{obj.code_date}B" if obj.code_date else ''
    
#     def validate(self, data):
#         """Validation : heure réelle = heure comptabilisée"""
#         heure_reelle_entree = data.get('heure_reelle_entree')
#         heure_reelle_sortie = data.get('heure_reelle_sortie')
#         heure_comp_entree = data.get('heure_comptabilisee_entree')
#         heure_comp_sortie = data.get('heure_comptabilisee_sortie')
        
#         # Si modification, les heures doivent être identiques
#         if heure_reelle_entree and heure_comp_entree:
#             if heure_reelle_entree != heure_comp_entree:
#                 raise serializers.ValidationError(
#                     "L'heure réelle d'entrée doit être identique à l'heure comptabilisée"
#                 )
        
#         if heure_reelle_sortie and heure_comp_sortie:
#             if heure_reelle_sortie != heure_comp_sortie:
#                 raise serializers.ValidationError(
#                     "L'heure réelle de sortie doit être identique à l'heure comptabilisée"
#                 )
        
#         # Si les heures sont corrigées et cohérentes, marquer comme OK
#         if heure_reelle_entree and heure_reelle_sortie:
#             if heure_reelle_entree < heure_reelle_sortie:
#                 data['etat'] = 'ok'
#                 data['corrigee'] = True
        
#         return data



# class AnomalieSerializer(serializers.ModelSerializer):
#     etat_display = serializers.CharField(source='get_etat_display', read_only=True)
#     user_name = serializers.SerializerMethodField()
#     badgenumber = serializers.SerializerMethodField()
#     est_corrigee = serializers.ReadOnlyField()
    
#     # Codes pour affichage
#     code_date_brut = serializers.SerializerMethodField()
#     code_date_reel = serializers.SerializerMethodField()
#     code_date_rectifie = serializers.SerializerMethodField()
    
#     class Meta:
#         model = Anomalie
#         fields = [
#             'id',
#             'userid',
#             'user_name',
#             'badgenumber',
#             'section',
#             'date',
#             'code_date',
#             'code_date_brut',
#             'code_date_reel',
#             'code_date_rectifie',
#             'heure_brute_entree',
#             'heure_brute_sortie',
#             'heure_reelle_entree',
#             'heure_reelle_sortie',
#             'heure_rectifiee_entree',
#             'heure_rectifiee_sortie',
#             'etat',
#             'etat_display',
#             'est_corrigee',
#             'commentaire',
#             'cree_le',
#             'modifie_le'
#         ]
#         read_only_fields = ['id', 'cree_le', 'modifie_le', 'heure_brute_entree', 'heure_brute_sortie', 'est_corrigee']
    
#     def get_user_name(self, obj):
#         """Récupère le nom de l'utilisateur"""
#         try:
#             from .models import UserInfo
#             user = UserInfo.objects.get(userid=obj.userid)
#             return user.name if user else f"User {obj.userid}"
#         except:
#             return f"User {obj.userid}"
    
#     def get_badgenumber(self, obj):
#         """Récupère le badgenumber"""
#         try:
#             from .models import UserInfo
#             user = UserInfo.objects.get(userid=obj.userid)
#             return user.badgenumber if user else None
#         except:
#             return None
    
#     def get_code_date_brut(self, obj):
#         """Code date avec heures brutes (non modifiable)"""
#         if obj.heure_brute_entree or obj.heure_brute_sortie:
#             return f"{obj.code_date}B" if obj.code_date else 'B'
#         return ''
    
#     def get_code_date_reel(self, obj):
#         """Code date avec heures réelles (horaires de section - modifiable)"""
#         if obj.heure_reelle_entree or obj.heure_reelle_sortie:
#             return f"{obj.code_date}R" if obj.code_date else 'R'
#         return ''
    
#     def get_code_date_rectifie(self, obj):
#         """Code date avec heures rectifiées (corrigées manuellement - modifiable)"""
#         if obj.heure_rectifiee_entree or obj.heure_rectifiee_sortie:
#             return f"{obj.code_date}P" if obj.code_date else 'P'
#         return ''
    
#     def validate(self, data):
#         """
#         Validation : vérifier la cohérence des heures
#         """
#         heure_rectifiee_entree = data.get('heure_rectifiee_entree')
#         heure_rectifiee_sortie = data.get('heure_rectifiee_sortie')
        
#         # Si les deux heures rectifiées sont renseignées, vérifier qu'elles sont cohérentes
#         if heure_rectifiee_entree and heure_rectifiee_sortie:
#             if heure_rectifiee_entree >= heure_rectifiee_sortie:
#                 raise serializers.ValidationError(
#                     "L'heure rectifiée d'entrée doit être antérieure à l'heure rectifiée de sortie"
#                 )
        
#         return data
    
#     def update(self, instance, validated_data):
#         """
#         Met à jour l'anomalie et recalcule automatiquement l'état
#         """
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
        
#         # L'état sera automatiquement mis à jour via le save() du modèle
#         instance.save()
        
#         return instance



class AnomalieSerializer(serializers.ModelSerializer):
    etat_display = serializers.CharField(source='get_etat_display', read_only=True)
    user_name = serializers.SerializerMethodField()
    badgenumber = serializers.SerializerMethodField()
    est_corrigee = serializers.ReadOnlyField()
    
    # Codes pour affichage
    code_date_brut = serializers.SerializerMethodField()
    code_date_reel = serializers.SerializerMethodField()
    code_date_rectifie = serializers.SerializerMethodField()
    
    class Meta:
        model = Anomalie
        fields = [
            'id',
            'userid',
            'user_name',
            'badgenumber',
            'section',
            'date',
            'code_date',
            'code_date_brut',
            'code_date_reel',
            'code_date_rectifie',
            'heure_brute_entree',
            'heure_brute_sortie',
            'heure_reelle_entree',
            'heure_reelle_sortie',
            'heure_rectifiee_entree',
            'heure_rectifiee_sortie',
            'etat',
            'etat_display',
            'est_corrigee',
            'commentaire',
            'cree_le',
            'modifie_le'
        ]
        read_only_fields = ['id', 'cree_le', 'modifie_le', 'heure_brute_entree', 'heure_brute_sortie', 'est_corrigee']
    
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
    
    def get_code_date_brut(self, obj):
        """Code date avec heures brutes (non modifiable)"""
        if obj.heure_brute_entree or obj.heure_brute_sortie:
            return f"{obj.code_date}B" if obj.code_date else 'B'
        return ''
    
    def get_code_date_reel(self, obj):
        """Code date avec heures réelles (horaires de section - modifiable)"""
        if obj.heure_reelle_entree or obj.heure_reelle_sortie:
            return f"{obj.code_date}R" if obj.code_date else 'R'
        return ''
    
    def get_code_date_rectifie(self, obj):
        """Code date avec heures rectifiées (corrigées manuellement - modifiable)"""
        if obj.heure_rectifiee_entree or obj.heure_rectifiee_sortie:
            return f"{obj.code_date}P" if obj.code_date else 'P'
        return ''
    
    def validate(self, data):
        """
        Validation : vérifier la cohérence des heures
        """
        heure_rectifiee_entree = data.get('heure_rectifiee_entree')
        heure_rectifiee_sortie = data.get('heure_rectifiee_sortie')
        
        # Si les deux heures rectifiées sont renseignées, vérifier qu'elles sont cohérentes
        if heure_rectifiee_entree and heure_rectifiee_sortie:
            if heure_rectifiee_entree >= heure_rectifiee_sortie:
                raise serializers.ValidationError(
                    "L'heure rectifiée d'entrée doit être antérieure à l'heure rectifiée de sortie"
                )
        
        return data
    
    def update(self, instance, validated_data):
        """
        Met à jour l'anomalie et recalcule automatiquement l'état
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # L'état sera automatiquement mis à jour via le save() du modèle
        instance.save()
        
        return instance
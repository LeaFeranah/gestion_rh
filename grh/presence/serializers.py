# from rest_framework import serializers
# from decimal import Decimal
# from .models import Date, HoraireSection, Evenement, Anomalie, HoraireException
# from .models import Date, HoraireSection, Evenement, Anomalie, HoraireException, PeriodeFermeture


# class DateSerializer(serializers.ModelSerializer):
#     code_affichage = serializers.ReadOnlyField()

#     class Meta:
#         model = Date
#         fields = ['date', 'code_date', 'code_affichage', 'hors_periode', 'mois_reference']


# class HoraireSectionSerializer(serializers.ModelSerializer):
#     heure_entree_normale              = serializers.ReadOnlyField()
#     heure_sortie_normale              = serializers.ReadOnlyField()
#     sortie_samedi_normale             = serializers.ReadOnlyField()
#     sortie_vendredi_paiement_normale  = serializers.ReadOnlyField()
#     sortie_samedi_paiement_normale    = serializers.ReadOnlyField()

#     class Meta:
#         model = HoraireSection
#         fields = [
#             'section',
#             'heure_entree',
#             'heure_sortie',
#             'sortie_samedi',
#             'sortie_vendredi_paiement',
#             'sortie_samedi_paiement',
#             'heure_entree_normale',
#             'heure_sortie_normale',
#             'sortie_samedi_normale',
#             'sortie_vendredi_paiement_normale',
#             'sortie_samedi_paiement_normale',
#         ]

#     def validate_sortie_vendredi_paiement(self, value):
#         try:
#             if isinstance(value, str):
#                 value = Decimal(value)
#             if not (0 <= float(value) < 24):
#                 raise serializers.ValidationError(
#                     "L'heure de sortie vendredi paiement doit être entre 0 et 24")
#             return value
#         except (ValueError, TypeError):
#             raise serializers.ValidationError("Format d'heure invalide")

#     def validate_sortie_samedi_paiement(self, value):
#         try:
#             if isinstance(value, str):
#                 value = Decimal(value)
#             if not (0 <= float(value) < 24):
#                 raise serializers.ValidationError(
#                     "L'heure de sortie samedi paiement doit être entre 0 et 24")
#             return value
#         except (ValueError, TypeError):
#             raise serializers.ValidationError("Format d'heure invalide")


# class EvenementSerializer(serializers.ModelSerializer):
#     type_evenement_display = serializers.CharField(
#         source='get_type_evenement_display', read_only=True)
#     user_name    = serializers.SerializerMethodField()
#     badgenumber  = serializers.SerializerMethodField()

#     class Meta:
#         model = Evenement
#         fields = [
#             'id', 'userid', 'user_name', 'badgenumber',
#             'date', 'type_evenement', 'type_evenement_display',
#             'commentaire', 'cree_le', 'modifie_le',
#         ]
#         read_only_fields = ['id', 'cree_le', 'modifie_le']

#     def get_user_name(self, obj):
#         try:
#             from .models import UserInfo
#             user = UserInfo.objects.get(userid=obj.userid)
#             return user.name if user else f"User {obj.userid}"
#         except:
#             return f"User {obj.userid}"

#     def get_badgenumber(self, obj):
#         try:
#             from .models import UserInfo
#             user = UserInfo.objects.get(userid=obj.userid)
#             return user.badgenumber if user else None
#         except:
#             return None

#     def validate_type_evenement(self, value):
#         valid_types = [choice[0] for choice in Evenement.TYPES_EVENEMENT]
#         if value not in valid_types:
#             raise serializers.ValidationError(
#                 f"Type d'événement invalide. Choix: {', '.join(valid_types)}")
#         return value


# class HoraireExceptionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model  = HoraireException
#         fields = ['id', 'date', 'section', 'heure_entree',
#                   'heure_sortie', 'motif', 'cree_le']
#         read_only_fields = ['id', 'cree_le']
        

# class AnomalieSerializer(serializers.ModelSerializer):
#     etat_display  = serializers.CharField(source='get_etat_display', read_only=True)
#     user_name     = serializers.SerializerMethodField()
#     badgenumber   = serializers.SerializerMethodField()
#     est_corrigee  = serializers.ReadOnlyField()

#     # Codes pour affichage
#     code_date_brut      = serializers.SerializerMethodField()
#     code_date_reel      = serializers.SerializerMethodField()
#     code_date_rectifie  = serializers.SerializerMethodField()

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
#             # Heures brutes (non modifiables)
#             'heure_brute_entree',
#             'heure_brute_sortie',
#             # Tous les pointages bruts du jour (pour multiples_pointages)
#             # Heures réelles (section)
#             'pointages_bruts_json',      
#             'heure_reelle_entree',
#             'heure_reelle_sortie',
#             # Heures rectifiées (modifiables)
#             'heure_rectifiee_entree',
#             'heure_rectifiee_sortie',
#             'etat',
#             'etat_display',
#             'est_corrigee',
#             'commentaire',
#             'cree_le',
#             'modifie_le',
#         ]
#         read_only_fields = [
#             'id', 'cree_le', 'modifie_le',
#             'heure_brute_entree', 'heure_brute_sortie',
#             'pointages_bruts_json',      # non modifiable depuis l'API
#             'est_corrigee',
#         ]



#     # def get_user_name(self, obj):
#     #     try:
#     #         from .models import UserInfo
#     #         from personnel.models import InformationPersonnelle
#     #         user = UserInfo.objects.get(userid=obj.userid)
#     #         try:
#     #             emp = InformationPersonnelle.objects.get(numero_matricule=user.badgenumber)
#     #             return emp.appellation or emp.nom_complet
#     #         except InformationPersonnelle.DoesNotExist:
#     #             pass
#     #         return user.name if user else f"User {obj.userid}"
#     #     except:
#     #         return f"User {obj.userid}"

#     # def get_badgenumber(self, obj):
#     #     try:
#     #         from .models import UserInfo
#     #         user = UserInfo.objects.get(userid=obj.userid)
#     #         return user.badgenumber if user else None
#     #     except:
#     #         return None

#     # REMPLACER les deux méthodes existantes PAR :

#     def get_user_name(self, obj):
#         # 1. Essayer la map pré-chargée (contexte)
#         userinfo_map = self.context.get('userinfo_map', {})
#         appellation_map = self.context.get('appellation_map', {})
        
#         user = userinfo_map.get(obj.userid)
#         badge = user.badgenumber if user else None
        
#         # 2. Appellation pré-chargée si dispo
#         if badge and badge in appellation_map:
#             return appellation_map[badge]
        
#         # 3. Fallback DB (cas sans contexte)
#         try:
#             from .models import UserInfo
#             if not user:
#                 user = UserInfo.objects.get(userid=obj.userid)
#             try:
#                 from personnel.models import InformationPersonnelle
#                 emp = InformationPersonnelle.objects.get(numero_matricule=user.badgenumber)
#                 return emp.appellation or emp.nom_complet
#             except InformationPersonnelle.DoesNotExist:
#                 pass
#             return user.name if user else f"User {obj.userid}"
#         except:
#             return f"User {obj.userid}"

#     def get_badgenumber(self, obj):
#         userinfo_map = self.context.get('userinfo_map', {})
#         user = userinfo_map.get(obj.userid)
#         if user:
#             return user.badgenumber
#         try:
#             from .models import UserInfo
#             user = UserInfo.objects.get(userid=obj.userid)
#             return user.badgenumber
#         except:
#             return None

#     def get_code_date_brut(self, obj):
#         if obj.heure_brute_entree or obj.heure_brute_sortie:
#             return f"{obj.code_date}B" if obj.code_date else 'B'
#         return ''

#     def get_code_date_reel(self, obj):
#         if obj.heure_reelle_entree or obj.heure_reelle_sortie:
#             return f"{obj.code_date}R" if obj.code_date else 'R'
#         return ''

#     def get_code_date_rectifie(self, obj):
#         if obj.heure_rectifiee_entree or obj.heure_rectifiee_sortie:
#             return f"{obj.code_date}P" if obj.code_date else 'P'
#         return ''

#     def validate(self, data):
#         heure_rectifiee_entree = data.get('heure_rectifiee_entree')
#         heure_rectifiee_sortie = data.get('heure_rectifiee_sortie')
#         if heure_rectifiee_entree and heure_rectifiee_sortie:
#             if heure_rectifiee_entree >= heure_rectifiee_sortie:
#                 raise serializers.ValidationError(
#                     "L'heure rectifiée d'entrée doit être antérieure à l'heure rectifiée de sortie")
#         return data

#     def update(self, instance, validated_data):
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.save()
#         return instance
    





# class PeriodeFermetureSerializer(serializers.ModelSerializer):
#     mois_nom = serializers.SerializerMethodField()

#     class Meta:
#         model  = PeriodeFermeture
#         fields = ['id', 'annee', 'mois', 'mois_nom', 'date_fermeture', 'motif',
#                   'cree_le', 'modifie_le']
#         read_only_fields = ['id', 'cree_le', 'modifie_le']

#     def get_mois_nom(self, obj):
#         mois_fr = ['Janvier','Février','Mars','Avril','Mai','Juin',
#                    'Juillet','Août','Septembre','Octobre','Novembre','Décembre']
#         return mois_fr[obj.mois - 1]

#     def validate(self, data):
#         annee          = data.get('annee',          getattr(self.instance, 'annee',          None))
#         mois           = data.get('mois',           getattr(self.instance, 'mois',           None))
#         date_fermeture = data.get('date_fermeture', getattr(self.instance, 'date_fermeture', None))

#         if annee and mois and date_fermeture:
#             from calendar import monthrange
#             from datetime import date as d_cls
#             last_day = monthrange(annee, mois)[1]
#             if not (d_cls(annee, mois, 1) <= date_fermeture <= d_cls(annee, mois, last_day)):
#                 raise serializers.ValidationError(
#                     f"La date de fermeture doit être dans le mois {mois}/{annee}."
#                 )
#         return data



from rest_framework import serializers
from decimal import Decimal
from .models import Date, HoraireSection, Evenement, Anomalie, HoraireException
from .models import Date, HoraireSection, Evenement, Anomalie, HoraireException, PeriodeFermeture


class DateSerializer(serializers.ModelSerializer):
    code_affichage = serializers.ReadOnlyField()

    class Meta:
        model = Date
        fields = ['date', 'code_date', 'code_affichage', 'hors_periode', 'mois_reference']


class HoraireSectionSerializer(serializers.ModelSerializer):
    heure_entree_normale              = serializers.ReadOnlyField()
    heure_sortie_normale              = serializers.ReadOnlyField()
    sortie_samedi_normale             = serializers.ReadOnlyField()
    sortie_vendredi_paiement_normale  = serializers.ReadOnlyField()
    sortie_samedi_paiement_normale    = serializers.ReadOnlyField()

    class Meta:
        model = HoraireSection
        fields = [
            'section',
            'heure_entree',
            'heure_sortie',
            'sortie_samedi',
            'sortie_vendredi_paiement',
            'sortie_samedi_paiement',
            'responsable',
            'heure_entree_normale',
            'heure_sortie_normale',
            'sortie_samedi_normale',
            'sortie_vendredi_paiement_normale',
            'sortie_samedi_paiement_normale',
        ]

    def validate_sortie_vendredi_paiement(self, value):
        try:
            if isinstance(value, str):
                value = Decimal(value)
            if not (0 <= float(value) < 24):
                raise serializers.ValidationError(
                    "L'heure de sortie vendredi paiement doit être entre 0 et 24")
            return value
        except (ValueError, TypeError):
            raise serializers.ValidationError("Format d'heure invalide")

    def validate_sortie_samedi_paiement(self, value):
        try:
            if isinstance(value, str):
                value = Decimal(value)
            if not (0 <= float(value) < 24):
                raise serializers.ValidationError(
                    "L'heure de sortie samedi paiement doit être entre 0 et 24")
            return value
        except (ValueError, TypeError):
            raise serializers.ValidationError("Format d'heure invalide")


class EvenementSerializer(serializers.ModelSerializer):
    type_evenement_display = serializers.CharField(
        source='get_type_evenement_display', read_only=True)
    user_name    = serializers.SerializerMethodField()
    badgenumber  = serializers.SerializerMethodField()

    class Meta:
        model = Evenement
        fields = [
            'id', 'userid', 'user_name', 'badgenumber',
            'date', 'type_evenement', 'type_evenement_display',
            'commentaire', 'cree_le', 'modifie_le',
        ]
        read_only_fields = ['id', 'cree_le', 'modifie_le']

    def get_user_name(self, obj):
        try:
            from .models import UserInfo
            user = UserInfo.objects.get(userid=obj.userid)
            return user.name if user else f"User {obj.userid}"
        except:
            return f"User {obj.userid}"

    def get_badgenumber(self, obj):
        try:
            from .models import UserInfo
            user = UserInfo.objects.get(userid=obj.userid)
            return user.badgenumber if user else None
        except:
            return None

    def validate_type_evenement(self, value):
        valid_types = [choice[0] for choice in Evenement.TYPES_EVENEMENT]
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Type d'événement invalide. Choix: {', '.join(valid_types)}")
        return value


class HoraireExceptionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = HoraireException
        fields = ['id', 'date', 'section', 'heure_entree',
                  'heure_sortie', 'motif', 'cree_le']
        read_only_fields = ['id', 'cree_le']
        

class AnomalieSerializer(serializers.ModelSerializer):
    etat_display  = serializers.CharField(source='get_etat_display', read_only=True)
    user_name     = serializers.SerializerMethodField()
    badgenumber   = serializers.SerializerMethodField()
    est_corrigee  = serializers.ReadOnlyField()

    # Codes pour affichage
    code_date_brut      = serializers.SerializerMethodField()
    code_date_reel      = serializers.SerializerMethodField()
    code_date_rectifie  = serializers.SerializerMethodField()

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
            # Heures brutes (non modifiables)
            'heure_brute_entree',
            'heure_brute_sortie',
            # Tous les pointages bruts du jour (pour multiples_pointages)
            # Heures réelles (section)
            'pointages_bruts_json',      
            'heure_reelle_entree',
            'heure_reelle_sortie',
            # Heures rectifiées (modifiables)
            'heure_rectifiee_entree',
            'heure_rectifiee_sortie',
            'etat',
            'etat_display',
            'est_corrigee',
            'commentaire',
            'cree_le',
            'modifie_le',
        ]
        read_only_fields = [
            'id', 'cree_le', 'modifie_le',
            'heure_brute_entree', 'heure_brute_sortie',
            'pointages_bruts_json',      # non modifiable depuis l'API
            'est_corrigee',
        ]



    # def get_user_name(self, obj):
    #     try:
    #         from .models import UserInfo
    #         from personnel.models import InformationPersonnelle
    #         user = UserInfo.objects.get(userid=obj.userid)
    #         try:
    #             emp = InformationPersonnelle.objects.get(numero_matricule=user.badgenumber)
    #             return emp.appellation or emp.nom_complet
    #         except InformationPersonnelle.DoesNotExist:
    #             pass
    #         return user.name if user else f"User {obj.userid}"
    #     except:
    #         return f"User {obj.userid}"

    # def get_badgenumber(self, obj):
    #     try:
    #         from .models import UserInfo
    #         user = UserInfo.objects.get(userid=obj.userid)
    #         return user.badgenumber if user else None
    #     except:
    #         return None

    # REMPLACER les deux méthodes existantes PAR :

    def get_user_name(self, obj):
        # 1. Essayer la map pré-chargée (contexte)
        userinfo_map = self.context.get('userinfo_map', {})
        appellation_map = self.context.get('appellation_map', {})
        
        user = userinfo_map.get(obj.userid)
        badge = user.badgenumber if user else None
        
        # 2. Appellation pré-chargée si dispo
        if badge and badge in appellation_map:
            return appellation_map[badge]
        
        # 3. Fallback DB (cas sans contexte)
        try:
            from .models import UserInfo
            if not user:
                user = UserInfo.objects.get(userid=obj.userid)
            try:
                from personnel.models import InformationPersonnelle
                emp = InformationPersonnelle.objects.get(numero_matricule=user.badgenumber)
                return emp.appellation or emp.nom_complet
            except InformationPersonnelle.DoesNotExist:
                pass
            return user.name if user else f"User {obj.userid}"
        except:
            return f"User {obj.userid}"

    def get_badgenumber(self, obj):
        userinfo_map = self.context.get('userinfo_map', {})
        user = userinfo_map.get(obj.userid)
        if user:
            return user.badgenumber
        try:
            from .models import UserInfo
            user = UserInfo.objects.get(userid=obj.userid)
            return user.badgenumber
        except:
            return None

    def get_code_date_brut(self, obj):
        if obj.heure_brute_entree or obj.heure_brute_sortie:
            return f"{obj.code_date}B" if obj.code_date else 'B'
        return ''

    def get_code_date_reel(self, obj):
        if obj.heure_reelle_entree or obj.heure_reelle_sortie:
            return f"{obj.code_date}R" if obj.code_date else 'R'
        return ''

    def get_code_date_rectifie(self, obj):
        if obj.heure_rectifiee_entree or obj.heure_rectifiee_sortie:
            return f"{obj.code_date}P" if obj.code_date else 'P'
        return ''

    def validate(self, data):
        heure_rectifiee_entree = data.get('heure_rectifiee_entree')
        heure_rectifiee_sortie = data.get('heure_rectifiee_sortie')
        if heure_rectifiee_entree and heure_rectifiee_sortie:
            if heure_rectifiee_entree >= heure_rectifiee_sortie:
                raise serializers.ValidationError(
                    "L'heure rectifiée d'entrée doit être antérieure à l'heure rectifiée de sortie")
        return data

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    





class PeriodeFermetureSerializer(serializers.ModelSerializer):
    mois_nom = serializers.SerializerMethodField()

    class Meta:
        model  = PeriodeFermeture
        fields = ['id', 'annee', 'mois', 'mois_nom', 'date_fermeture', 'motif',
                  'cree_le', 'modifie_le']
        read_only_fields = ['id', 'cree_le', 'modifie_le']

    def get_mois_nom(self, obj):
        mois_fr = ['Janvier','Février','Mars','Avril','Mai','Juin',
                   'Juillet','Août','Septembre','Octobre','Novembre','Décembre']
        return mois_fr[obj.mois - 1]

    def validate(self, data):
        annee          = data.get('annee',          getattr(self.instance, 'annee',          None))
        mois           = data.get('mois',           getattr(self.instance, 'mois',           None))
        date_fermeture = data.get('date_fermeture', getattr(self.instance, 'date_fermeture', None))

        if annee and mois and date_fermeture:
            from calendar import monthrange
            from datetime import date as d_cls
            last_day = monthrange(annee, mois)[1]
            if not (d_cls(annee, mois, 1) <= date_fermeture <= d_cls(annee, mois, last_day)):
                raise serializers.ValidationError(
                    f"La date de fermeture doit être dans le mois {mois}/{annee}."
                )
        return data
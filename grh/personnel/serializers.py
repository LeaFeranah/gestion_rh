# # from rest_framework import serializers
# # from .models import Employe, Poste, Banque, Social, Identite, Document

# # # Serializer pour les documents
# # class DocumentSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = Document
# #         fields = ['id', 'type_document', 'fichier', 'date_ajout']

# # # Serializers pour les OneToOne
# # class PosteSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = Poste
# #         fields = ['titre_poste', 'date_embauche', 'type_contrat', 'salaire']

# # class BanqueSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = Banque
# #         fields = ['nom_banque', 'numero_compte', 'iban']

# # class SocialSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = Social
# #         fields = ['num_cnaps', 'num_ostie', 'assurance_sante']

# # class IdentiteSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = Identite
# #         fields = ['num_carte_identite', 'date_naissance', 'lieu_naissance', 'adresse']

# # # Serializer principal Employe avec relations imbriquées
# # class EmployeSerializer(serializers.ModelSerializer):
# #     poste = PosteSerializer(required=False)
# #     banque = BanqueSerializer(required=False)
# #     social = SocialSerializer(required=False)
# #     identite = IdentiteSerializer(required=False)
# #     documents = DocumentSerializer(many=True, read_only=True)

# #     class Meta:
# #         model = Employe
# #         fields = [
# #             'id', 'matricule', 'nom', 'prenoms', 'fonction', 'section', 'appelation', 
# #             'email', 'telephone', 'poste', 'banque', 'social', 'identite', 'documents'
# #         ]

# #     def create(self, validated_data):
# #         poste_data = validated_data.pop('poste', None)
# #         banque_data = validated_data.pop('banque', None)
# #         social_data = validated_data.pop('social', None)
# #         identite_data = validated_data.pop('identite', None)

# #         employe = Employe.objects.create(**validated_data)

# #         if poste_data:
# #             Poste.objects.create(employe=employe, **poste_data)
# #         if banque_data:
# #             Banque.objects.create(employe=employe, **banque_data)
# #         if social_data:
# #             Social.objects.create(employe=employe, **social_data)
# #         if identite_data:
# #             Identite.objects.create(employe=employe, **identite_data)

# #         return employe

# #     def update(self, instance, validated_data):
# #         poste_data = validated_data.pop('poste', None)
# #         banque_data = validated_data.pop('banque', None)
# #         social_data = validated_data.pop('social', None)
# #         identite_data = validated_data.pop('identite', None)

# #         for attr, value in validated_data.items():
# #             setattr(instance, attr, value)
# #         instance.save()

# #         if poste_data:
# #             Poste.objects.update_or_create(employe=instance, defaults=poste_data)
# #         if banque_data:
# #             Banque.objects.update_or_create(employe=instance, defaults=banque_data)
# #         if social_data:
# #             Social.objects.update_or_create(employe=instance, defaults=social_data)
# #         if identite_data:
# #             Identite.objects.update_or_create(employe=instance, defaults=identite_data)

# #         return instance


# # from rest_framework import serializers
# # from .models import *

# # class InformationPersonnelleSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = InformationPersonnelle
# #         fields = '__all__'

# # class InformationProfessionnelleSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = InformationProfessionnelle
# #         fields = '__all__'

# # class InformationBancaireSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = InformationBancaire
# #         fields = '__all__'

# # class InformationSocialeSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = InformationSociale
# #         fields = '__all__'

# # class InformationComplementaireSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = InformationComplementaire
# #         fields = '__all__'



# # from rest_framework import serializers
# # from .models import *

# # class InformationProfessionnelleSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = InformationProfessionnelle
# #         fields = '__all__'

# # class InformationBancaireSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = InformationBancaire
# #         fields = '__all__'

# # class InformationSocialeSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = InformationSociale
# #         fields = '__all__'

# # class InformationComplementaireSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = InformationComplementaire
# #         fields = '__all__'

# # class InformationPersonnelleSerializer(serializers.ModelSerializer):
# #     professionnelle = InformationProfessionnelleSerializer(read_only=True)
# #     bancaire = InformationBancaireSerializer(read_only=True)
# #     sociale = InformationSocialeSerializer(read_only=True)
# #     complementaire = InformationComplementaireSerializer(read_only=True)

# #     class Meta:
# #         model = InformationPersonnelle
# #         fields = '__all__'




# # from rest_framework import serializers
# # from .models import *

# # class InformationProfessionnelleSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = InformationProfessionnelle
# #         fields = '__all__'
# #         extra_kwargs = {field: {'required': False} for field in fields}


# # class InformationBancaireSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = InformationBancaire
# #         fields = '__all__'
# #         extra_kwargs = {field: {'required': False} for field in fields}


# # class InformationSocialeSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = InformationSociale
# #         fields = '__all__'
# #         extra_kwargs = {field: {'required': False} for field in fields}


# # class InformationComplementaireSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = InformationComplementaire
# #         fields = '__all__'
# #         extra_kwargs = {field: {'required': False} for field in fields}


# # class InformationPersonnelleSerializer(serializers.ModelSerializer):
# #     professionnelle = InformationProfessionnelleSerializer(read_only=True)
# #     bancaire = InformationBancaireSerializer(read_only=True)
# #     sociale = InformationSocialeSerializer(read_only=True)
# #     complementaire = InformationComplementaireSerializer(read_only=True)

# #     class Meta:
# #         model = InformationPersonnelle
# #         fields = '__all__'
# #         extra_kwargs = {
# #             'numero_matricule': {'required': True},
# #             'nom': {'required': True},
# #             'prenoms': {'required': True},
# #             # Tous les autres sont facultatifs
# #         }





# # from rest_framework import serializers
# # from .models import *
# # from .models import DossierPersonnel

# # class DossierPersonnelSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = DossierPersonnel
# #         fields = '__all__'

# # # ----------------- Sous-objets -----------------
# # class InformationProfessionnelleSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = InformationProfessionnelle
# #         fields = '__all__'
# #         extra_kwargs = {field: {'required': False} for field in fields}

# # class InformationBancaireSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = InformationBancaire
# #         fields = '__all__'
# #         extra_kwargs = {field: {'required': False} for field in fields}

# # class InformationSocialeSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = InformationSociale
# #         fields = '__all__'
# #         extra_kwargs = {field: {'required': False} for field in fields}

# # # class InformationComplementaireSerializer(serializers.ModelSerializer):
# # #     class Meta:
# # #         model = InformationComplementaire
# # #         fields = '__all__'
# # #         extra_kwargs = {field: {'required': False} for field in fields}


# # # ----------------- Nouveaux serializers -----------------
# # # 🔹 Enfants
# # # ----------------- Informations Salaire -----------------
# # class InformationSalairePersonnelSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = InformationSalairePersonnel
# #         fields = '__all__'
# #         extra_kwargs = {field: {'required': False} for field in fields}

# # class EnfantSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = Enfant
# #         fields = '__all__'
# #         extra_kwargs = {field: {'required': False} for field in fields}


# # # 🔹 Informations Familiales (avec enfants inclus)
# # class InformationFamilialeSerializer(serializers.ModelSerializer):
# #     enfants = EnfantSerializer(many=True, read_only=True)  # liste des enfants associés

# #     class Meta:
# #         model = InformationFamiliale
# #         fields = '__all__'
# #         extra_kwargs = {field: {'required': False} for field in fields}

# # # ----------------- Employee serializer -----------------
# # # Pour GET/POST (affiche objets liés)
# # class InformationPersonnelleSerializer(serializers.ModelSerializer):
# #     professionnelle = InformationProfessionnelleSerializer(read_only=True, required=False)
# #     bancaire = InformationBancaireSerializer(read_only=True, required=False)
# #     sociale = InformationSocialeSerializer(read_only=True, required=False)
# #     #complementaire = InformationComplementaireSerializer(read_only=True, required=False)
# #     familiale = InformationFamilialeSerializer(read_only=True)
# #     salaire_personnel = InformationSalairePersonnelSerializer(read_only=True)


# #     class Meta:
# #         model = InformationPersonnelle
# #         fields = '__all__'
# #         extra_kwargs = {
# #             'numero_matricule': {'required': True},
# #             'nom': {'required': True},
# #             'prenoms': {'required': True},
# #         }

# # # Serializer minimal pour PUT/UPDATE (évite erreur 500)
# # class InformationPersonnellePUTSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = InformationPersonnelle
# #         fields = '__all__'
# #         extra_kwargs = {
# #             'numero_matricule': {'required': True},
# #             'nom': {'required': True},
# #             'prenoms': {'required': True},
# #         }





# from rest_framework import serializers
# from .models import *

# # ----------------- Dossier Personnel -----------------
# class DossierPersonnelSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = DossierPersonnel
#         fields = '__all__'


# class InformationBancaireSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = InformationBancaire
#         fields = '__all__'
#         extra_kwargs = {field: {'required': False} for field in fields}

# class InformationSocialeSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = InformationSociale
#         fields = '__all__'
#         extra_kwargs = {field: {'required': False} for field in fields}

# # ----------------- Informations Salaire -----------------
# class InformationSalairePersonnelSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = InformationSalairePersonnel
#         fields = '__all__'
#         extra_kwargs = {field: {'required': False} for field in fields}

# class EnfantSerializer(serializers.ModelSerializer):
#     # 🔹 Calcul de l'âge avec personnalisation
#     age = serializers.SerializerMethodField()
    
#     class Meta:
#         model = Enfant
#         fields = '__all__'
#         extra_kwargs = {field: {'required': False} for field in fields}
    
#     def get_age(self, obj):
#         if obj.date_naissance:
#             today = date.today()
#             age = today.year - obj.date_naissance.year - (
#                 (today.month, today.day) < (obj.date_naissance.month, obj.date_naissance.day)
#             )
#             return f"{age} ans"
#         return "Non spécifié"


# class InformationFamilialeSerializer(serializers.ModelSerializer):
#     enfants = EnfantSerializer(many=True, required=False)

#     class Meta:
#         model = InformationFamiliale
#         fields = '__all__'
#         extra_kwargs = {field: {'required': False} for field in fields}

#     # Les méthodes create et update restent inchangées
#     def create(self, validated_data):
#         enfants_data = validated_data.pop('enfants', [])
#         familiale = InformationFamiliale.objects.create(**validated_data)
#         for enfant_data in enfants_data:
#             Enfant.objects.create(familiale=familiale, **enfant_data)
#         return familiale

#     def update(self, instance, validated_data):
#         enfants_data = validated_data.pop('enfants', None)
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.save()

#         if enfants_data is not None:
#             instance.enfants.all().delete()
#             for enfant_data in enfants_data:
#                 Enfant.objects.create(familiale=instance, **enfant_data)
#         return instance


# # ----------------- Employee -----------------
# class InformationPersonnelleSerializer(serializers.ModelSerializer):
#     bancaire = InformationBancaireSerializer(read_only=True)
#     sociale = InformationSocialeSerializer(read_only=True)
#     familiale = InformationFamilialeSerializer(read_only=True)
#     salaire_personnel = InformationSalairePersonnelSerializer(read_only=True)

#     class Meta:
#         model = InformationPersonnelle
#         fields = '__all__'
#         extra_kwargs = {
#             'numero_matricule': {'required': True},
#             'nom': {'required': True},
#             'prenoms': {'required': True},
#         }


# # Serializer minimal pour PUT/UPDATE (évite erreur 500)
# class InformationPersonnellePUTSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = InformationPersonnelle
#         fields = '__all__'
#         extra_kwargs = {
#             'numero_matricule': {'required': True},
#             'nom': {'required': True},
#             'prenoms': {'required': True},
#         }



from rest_framework import serializers
from .models import *
from datetime import date

# ----------------- Dossier Personnel -----------------
class DossierPersonnelSerializer(serializers.ModelSerializer):
    class Meta:
        model = DossierPersonnel
        fields = '__all__'

class InformationBancaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = InformationBancaire
        fields = '__all__'
        extra_kwargs = {field: {'required': False} for field in fields}

class InformationSocialeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InformationSociale
        fields = '__all__'
        extra_kwargs = {field: {'required': False} for field in fields}

class InformationSalairePersonnelSerializer(serializers.ModelSerializer):
    class Meta:
        model = InformationSalairePersonnel
        fields = '__all__'
        extra_kwargs = {field: {'required': False} for field in fields}

class EnfantSerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField()
    
    class Meta:
        model = Enfant
        fields = '__all__'
        extra_kwargs = {field: {'required': False} for field in fields}
    
    def get_age(self, obj):
        if obj.date_naissance:
            today = date.today()
            age = today.year - obj.date_naissance.year - (
                (today.month, today.day) < (obj.date_naissance.month, obj.date_naissance.day)
            )
            return f"{age} ans"
        return "Non spécifié"

class InformationFamilialeSerializer(serializers.ModelSerializer):
    enfants = EnfantSerializer(many=True, required=False)

    class Meta:
        model = InformationFamiliale
        fields = '__all__'
        extra_kwargs = {field: {'required': False} for field in fields}

    def create(self, validated_data):
        enfants_data = validated_data.pop('enfants', [])
        familiale = InformationFamiliale.objects.create(**validated_data)
        for enfant_data in enfants_data:
            Enfant.objects.create(familiale=familiale, **enfant_data)
        return familiale

    def update(self, instance, validated_data):
        enfants_data = validated_data.pop('enfants', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if enfants_data is not None:
            instance.enfants.all().delete()
            for enfant_data in enfants_data:
                Enfant.objects.create(familiale=instance, **enfant_data)
        return instance

# ----------------- Employee -----------------
class InformationPersonnelleSerializer(serializers.ModelSerializer):
    bancaire = InformationBancaireSerializer(read_only=True)
    sociale = InformationSocialeSerializer(read_only=True)
    familiale = InformationFamilialeSerializer(read_only=True)
    salaire_personnel = InformationSalairePersonnelSerializer(read_only=True)
    age = serializers.SerializerMethodField()
    retraite = serializers.SerializerMethodField()  
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)  # 

    class Meta:
        model = InformationPersonnelle
        fields = '__all__'
        extra_kwargs = {
            'numero_matricule': {'required': True},
            'nom': {'required': True},
            'prenoms': {'required': True},
            'created_by': {'read_only': True} 
        }

    
    def get_age(self, obj):
        if obj.age is not None:
            return f"{obj.age} ans"
        return "Non spécifié"
    
    def get_retraite(self, obj):
        return obj.retraite  # 🔹 Retourne directement la valeur calculée

class InformationPersonnellePUTSerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField(read_only=True)
    retraite = serializers.SerializerMethodField(read_only=True)  # 🔹 Nouveau champ

    class Meta:
        model = InformationPersonnelle
        fields = '__all__'
        extra_kwargs = {
            'numero_matricule': {'required': True},
            'nom': {'required': True},
            'prenoms': {'required': True},
        }
    
    def get_age(self, obj):
        if obj.age is not None:
            return f"{obj.age} ans"
        return "Non spécifié"
    
    def get_retraite(self, obj):
        return obj.retraite  # 🔹 Retourne directement la valeur calculée
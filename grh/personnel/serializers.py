from rest_framework import serializers
from .models import Employe, Poste, Banque, Social, Identite, Document

# Serializer pour les documents
class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'type_document', 'fichier', 'date_ajout']

# Serializers pour les OneToOne
class PosteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poste
        fields = ['titre_poste', 'date_embauche', 'type_contrat', 'salaire']

class BanqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banque
        fields = ['nom_banque', 'numero_compte', 'iban']

class SocialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Social
        fields = ['num_cnaps', 'num_ostie', 'assurance_sante']

class IdentiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Identite
        fields = ['num_carte_identite', 'date_naissance', 'lieu_naissance', 'adresse']

# Serializer principal Employe avec relations imbriquées
class EmployeSerializer(serializers.ModelSerializer):
    poste = PosteSerializer(required=False)
    banque = BanqueSerializer(required=False)
    social = SocialSerializer(required=False)
    identite = IdentiteSerializer(required=False)
    documents = DocumentSerializer(many=True, read_only=True)

    class Meta:
        model = Employe
        fields = [
            'id', 'matricule', 'nom', 'prenoms', 'fonction', 'section', 'appelation', 
            'email', 'telephone', 'poste', 'banque', 'social', 'identite', 'documents'
        ]

    def create(self, validated_data):
        poste_data = validated_data.pop('poste', None)
        banque_data = validated_data.pop('banque', None)
        social_data = validated_data.pop('social', None)
        identite_data = validated_data.pop('identite', None)

        employe = Employe.objects.create(**validated_data)

        if poste_data:
            Poste.objects.create(employe=employe, **poste_data)
        if banque_data:
            Banque.objects.create(employe=employe, **banque_data)
        if social_data:
            Social.objects.create(employe=employe, **social_data)
        if identite_data:
            Identite.objects.create(employe=employe, **identite_data)

        return employe

    def update(self, instance, validated_data):
        poste_data = validated_data.pop('poste', None)
        banque_data = validated_data.pop('banque', None)
        social_data = validated_data.pop('social', None)
        identite_data = validated_data.pop('identite', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if poste_data:
            Poste.objects.update_or_create(employe=instance, defaults=poste_data)
        if banque_data:
            Banque.objects.update_or_create(employe=instance, defaults=banque_data)
        if social_data:
            Social.objects.update_or_create(employe=instance, defaults=social_data)
        if identite_data:
            Identite.objects.update_or_create(employe=instance, defaults=identite_data)

        return instance

from django.db.models import fields
from rest_framework import serializers
from .models import Departement, Service, Section, Fonction, InfoSociete as Societe, Hierarchie, Organe


class SocieteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Societe
        #fields = '__all__'
        fields = ['id', 'name', 'adresse', 'raison_social', 'rcs', 'nif', 'stat', 'ostie', 'cnaps', 'telephone', 'email']

class DepartementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departement
        fields = ['id', 'name', 'societe']
        #fields = '__all__'

class ServiceSerializer( serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'departement']
        #fields = '__all__'

class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ['id', 'name', 'service']

class OrganeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organe
        fields = ['id','nom_organe','societe','hierarchie']

class HierarchieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hierarchie
        fields = ['id', 'nom_poste']
class FonctionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fonction
        fields = '__all__'

#class InfoSocieteSerializer(serializers.HyperlinkedModelSeriali)

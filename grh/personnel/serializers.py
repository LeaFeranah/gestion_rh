from rest_framework import serializers
from .models import *
from datetime import date


# ----------------- Information Professionnelle -----------------
class InformationProfessionnelleSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = InformationProfessionnelle
        fields = '__all__'
        extra_kwargs = {field: {'required': False} for field in fields}
    
    

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
    information_professionnelle = InformationProfessionnelleSerializer(read_only=True)
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
    retraite = serializers.SerializerMethodField(read_only=True)  

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
        return obj.retraite  
    


class HistoriqueSalaireSerializer(serializers.ModelSerializer):
    modifie_par_nom = serializers.CharField(source='modifie_par.get_full_name', read_only=True)
    employe_nom = serializers.CharField(source='employe.nom_complet', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = HistoriqueSalaire
        fields = '__all__'
        read_only_fields = ['modifie_par']











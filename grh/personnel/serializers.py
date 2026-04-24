
from rest_framework import serializers
from .models import *
from datetime import date


# ----------------- Evolution de Poste -----------------
class EvolutionPosteSerializer(serializers.ModelSerializer):
    """Serializer pour les évolutions de poste"""
    employe_nom = serializers.CharField(source='employe.nom_complet', read_only=True)
    modifie_par_nom = serializers.CharField(source='modifie_par.get_full_name', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    
    class Meta:
        model = EvolutionPoste
        fields = '__all__'
        read_only_fields = [
            'ancienne_categorie', 'ancienne_fonction', 
            'ancienne_section', 'ancien_responsable',
            'modifie_par', 'created_at', 'updated_at'
        ]
    
    def validate(self, data):
        """Validation personnalisée pour l'évolution de poste"""
        employe = data.get('employe')
        
        # Vérifier que l'employé a une information professionnelle
        if not hasattr(employe, 'information_professionnelle'):
            raise serializers.ValidationError(
                "L'employé doit avoir une information professionnelle avant de créer une évolution de poste"
            )
        
        return data
    
    def create(self, validated_data):
        """Créer une évolution de poste avec capture des anciennes valeurs"""
        request = self.context.get('request')
        employe = validated_data.get('employe')
        
        # Capturer les anciennes valeurs depuis l'InformationProfessionnelle
        info_pro = employe.information_professionnelle
        
        validated_data['ancienne_categorie'] = info_pro.categorie
        validated_data['ancienne_fonction'] = info_pro.fonction
        validated_data['ancienne_section'] = info_pro.section
        validated_data['ancien_responsable'] = info_pro.responsable
        
        # Assigner l'utilisateur connecté
        if request and hasattr(request, 'user'):
            validated_data['modifie_par'] = request.user
        
        return super().create(validated_data)


# ----------------- Information Professionnelle -----------------
class InformationProfessionnelleCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la CRÉATION de l'InformationProfessionnelle"""
    class Meta:
        model = InformationProfessionnelle
        fields = '__all__'
        extra_kwargs = {
            'employe': {'required': True},
        }


class InformationProfessionnelleUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la MISE À JOUR de l'InformationProfessionnelle (exclut les champs sensibles)"""
    class Meta:
        model = InformationProfessionnelle
        exclude = ['categorie', 'fonction', 'section', 'responsable']
        read_only_fields = ['employe']


class InformationProfessionnelleSerializer(serializers.ModelSerializer):
    """Serializer pour la LECTURE de l'InformationProfessionnelle (avec toutes les infos)"""
    derniere_evolution = serializers.SerializerMethodField()
    evolutions_poste = EvolutionPosteSerializer(many=True, read_only=True)
    
    class Meta:
        model = InformationProfessionnelle
        fields = '__all__'
    
    def get_derniere_evolution(self, obj):
        """Récupère la dernière évolution de poste appliquée"""
        derniere = obj.employe.evolutions_poste.filter(statut='REALISEE').order_by('-date_evolution').first()
        if derniere:
            return EvolutionPosteSerializer(derniere).data
        return None


# ----------------- Dossier Personnel -----------------
class DossierPersonnelSerializer(serializers.ModelSerializer):
    class Meta:
        model = DossierPersonnel
        fields = '__all__'


# ----------------- Information Bancaire -----------------
class InformationBancaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = InformationBancaire
        fields = '__all__'
        extra_kwargs = {field: {'required': False} for field in fields}


# ----------------- Information Sociale -----------------
class InformationSocialeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InformationSociale
        fields = '__all__'
        extra_kwargs = {field: {'required': False} for field in fields}


# ----------------- Information Salaire -----------------
class InformationSalairePersonnelSerializer(serializers.ModelSerializer):
    categorie = serializers.CharField(source='employe.information_professionnelle.categorie', read_only=True)
    
    class Meta:
        model = InformationSalairePersonnel
        fields = '__all__'
        extra_kwargs = {field: {'required': False} for field in fields}


# ----------------- Enfant -----------------
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


# ----------------- Information Familiale -----------------
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


# ----------------- Employé -----------------
class InformationPersonnelleSerializer(serializers.ModelSerializer):
    bancaire = InformationBancaireSerializer(read_only=True)
    sociale = InformationSocialeSerializer(read_only=True)
    familiale = InformationFamilialeSerializer(read_only=True)
    salaire_personnel = InformationSalairePersonnelSerializer(read_only=True)
    information_professionnelle = InformationProfessionnelleSerializer(read_only=True)
    age = serializers.SerializerMethodField()
    retraite = serializers.SerializerMethodField()  
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    evolutions_poste = EvolutionPosteSerializer(many=True, read_only=True)

    class Meta:
        model = InformationPersonnelle
        fields = '__all__'
        extra_kwargs = {
            'numero_matricule': {'required': True},
            'nom_complet': {'required': True},
            'created_by': {'read_only': True} 
        }
    
    def get_age(self, obj):
        if obj.age is not None:
            return f"{obj.age} ans"
        return "Non spécifié"
    
    def get_retraite(self, obj):
        return obj.retraite


class InformationPersonnellePUTSerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField(read_only=True)
    retraite = serializers.SerializerMethodField(read_only=True)  

    class Meta:
        model = InformationPersonnelle
        fields = '__all__'
        extra_kwargs = {
            'numero_matricule': {'required': True},
            'nom_complet': {'required': True},
        }
    
    def get_age(self, obj):
        if obj.age is not None:
            return f"{obj.age} ans"
        return "Non spécifié"
    
    def get_retraite(self, obj):
        return obj.retraite


# ----------------- Historique Salaire -----------------
class HistoriqueSalaireSerializer(serializers.ModelSerializer):
    modifie_par_nom = serializers.CharField(source='modifie_par.get_full_name', read_only=True)
    employe_nom = serializers.CharField(source='employe.nom_complet', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = HistoriqueSalaire
        fields = '__all__'
        read_only_fields = ['modifie_par']



class InformationPersonnelleLightSerializer(serializers.ModelSerializer):
    """Serializer léger pour la liste — pas de relations imbriquées lourdes"""
    fonction = serializers.CharField(
        source='information_professionnelle.fonction', read_only=True, default=None
    )
    section = serializers.CharField(
        source='information_professionnelle.section', read_only=True, default=None
    )
    responsable_section = serializers.CharField(
        source='information_professionnelle.responsable_section', read_only=True, default=None
    )

    class Meta:
        model = InformationPersonnelle
        fields = [
            'id', 'numero_matricule', 'nom_complet', 'sexe',
            'appellation', 'photo', 'depart',
            'fonction', 'section', 'responsable_section',
        ]
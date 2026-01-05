# from rest_framework import serializers

# class PresenceSerializer(serializers.Serializer):
#     badgenumber = serializers.CharField()
#     name = serializers.CharField()
#     date = serializers.DateField()
#     heure_entree = serializers.TimeField(allow_null=True)
#     heure_sortie = serializers.TimeField(allow_null=True)
#     evenement = serializers.CharField()


# presence/serializers.py
from rest_framework import serializers
from .models import Date

class DateSerializer(serializers.ModelSerializer):
    code_affichage = serializers.CharField(read_only=True)  # 11F ou 11
    mois_nom = serializers.SerializerMethodField()
    
    class Meta:
        model = Date
        fields = ['date', 'code_date', 'hors_periode', 'code_affichage', 'mois_reference', 'mois_nom']
    
    def get_mois_nom(self, obj):
        mois_fr = [
            'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
        ]
        return f"{mois_fr[obj.mois_reference.month - 1]} {obj.mois_reference.year}"


class PresenceSerializer(serializers.Serializer):
    badgenumber = serializers.CharField()
    name = serializers.CharField()
    date = serializers.DateField()
    code_date = serializers.CharField()  # 11, 12, etc.
    code_affichage = serializers.CharField()  # 11F ou 11
    hors_periode = serializers.BooleanField()
    heure_entree = serializers.TimeField(allow_null=True)
    heure_sortie = serializers.TimeField(allow_null=True)
    evenement = serializers.CharField()
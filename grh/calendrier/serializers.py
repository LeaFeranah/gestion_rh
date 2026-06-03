from rest_framework import serializers
from .models import Calendrier, JourFerie
from datetime import date


class JourFerieSerializer(serializers.ModelSerializer):
    cree_par_nom = serializers.CharField(source='cree_par.get_full_name', read_only=True)
    type_jour_display = serializers.CharField(source='get_type_jour_display', read_only=True)
    couleur_display = serializers.CharField(source='get_couleur_display', read_only=True)
    est_passe = serializers.SerializerMethodField()
    jour_semaine = serializers.SerializerMethodField()

    class Meta:
        model = JourFerie
        fields = [
            'id', 'calendrier', 'titre', 'date', 'type_jour', 'type_jour_display',
            'couleur', 'couleur_display', 'est_recurrent', 'description',
            'cree_par', 'cree_par_nom', 'cree_le', 'modifie_le',
            'est_passe', 'jour_semaine',
        ]
        read_only_fields = ['id', 'cree_par', 'cree_le', 'modifie_le']

    def get_est_passe(self, obj):
        return obj.date < date.today()

    def get_jour_semaine(self, obj):
        jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        return jours[obj.date.weekday()]

    def validate_date(self, value):
        # Vérifie cohérence avec l'année du calendrier
        calendrier_id = (
            self.initial_data.get('calendrier') or
            (self.instance.calendrier_id if self.instance else None)
        )
        if calendrier_id:
            try:
                cal = Calendrier.objects.get(pk=calendrier_id)
                if value.year != cal.annee:
                    raise serializers.ValidationError(
                        f"La date doit être dans l'année {cal.annee}."
                    )
            except Calendrier.DoesNotExist:
                pass
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['cree_par'] = request.user
        return super().create(validated_data)


class CalendrierSerializer(serializers.ModelSerializer):
    jours_feries = JourFerieSerializer(many=True, read_only=True)
    cree_par_nom = serializers.CharField(source='cree_par.get_full_name', read_only=True)
    nb_jours_feries = serializers.SerializerMethodField()
    prochain_jour = serializers.SerializerMethodField()

    class Meta:
        model = Calendrier
        fields = [
            'id', 'titre', 'annee', 'description',
            'cree_par', 'cree_par_nom', 'cree_le', 'modifie_le',
            'jours_feries', 'nb_jours_feries', 'prochain_jour',
        ]
        read_only_fields = ['id', 'cree_par', 'cree_le', 'modifie_le']

    def get_nb_jours_feries(self, obj):
        return obj.jours_feries.count()

    def get_prochain_jour(self, obj):
        today = date.today()
        prochain = obj.jours_feries.filter(date__gte=today).order_by('date').first()
        if prochain:
            return {
                'titre': prochain.titre,
                'date': prochain.date,
                'couleur': prochain.couleur,
                'type_jour': prochain.type_jour,
            }
        return None

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['cree_par'] = request.user
        return super().create(validated_data)


class CalendrierLightSerializer(serializers.ModelSerializer):
    """Version légère sans les jours fériés imbriqués"""
    nb_jours_feries = serializers.SerializerMethodField()
    cree_par_nom = serializers.CharField(source='cree_par.get_full_name', read_only=True)
    prochain_jour = serializers.SerializerMethodField()

    class Meta:
        model = Calendrier
        fields = [
            'id', 'titre', 'annee', 'description',
            'cree_par', 'cree_par_nom', 'cree_le', 'modifie_le',
            'nb_jours_feries', 'prochain_jour',
        ]

    def get_nb_jours_feries(self, obj):
        return obj.jours_feries.count()

    def get_prochain_jour(self, obj):
        today = date.today()
        prochain = obj.jours_feries.filter(date__gte=today).order_by('date').first()
        if prochain:
            return {
                'titre': prochain.titre,
                'date': prochain.date,
                'couleur': prochain.couleur,
            }
        return None
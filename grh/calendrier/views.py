from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from datetime import date

from .models import Calendrier, JourFerie
from .serializers import (
    CalendrierSerializer, CalendrierLightSerializer, JourFerieSerializer
)


# ─── Permission helper ─────────────────────────────────────────────────────────

class IsAdminOrReadOnly:
    """Tout utilisateur authentifié peut lire, seuls les admins peuvent écrire."""
    pass


# ─── Calendrier Views ──────────────────────────────────────────────────────────

class CalendrierListAPIView(APIView):
    """
    GET  /api/calendrier/                → liste tous les calendriers (tous les connectés)
    POST /api/calendrier/               → créer un calendrier (admin seulement)
    """
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        annee = request.query_params.get('annee')
        qs = Calendrier.objects.all().order_by('-annee', 'titre')
        if annee:
            qs = qs.filter(annee=int(annee))

        serializer = CalendrierLightSerializer(qs, many=True)
        return Response({
            'count': qs.count(),
            'calendriers': serializer.data,
        })

    def post(self, request):
        if not request.user.is_staff:
            return Response(
                {'error': "Accès réservé aux administrateurs."},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = CalendrierSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            obj = serializer.save()
            return Response(
                CalendrierSerializer(obj, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CalendrierDetailAPIView(APIView):
    """
    GET    /api/calendrier/<pk>/   → détail avec jours fériés (tous les connectés)
    PATCH  /api/calendrier/<pk>/   → modifier (admin seulement)
    DELETE /api/calendrier/<pk>/   → supprimer (admin seulement)
    """
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        obj = get_object_or_404(Calendrier, pk=pk)
        serializer = CalendrierSerializer(obj, context={'request': request})
        return Response(serializer.data)

    def patch(self, request, pk):
        if not request.user.is_staff:
            return Response(
                {'error': "Accès réservé aux administrateurs."},
                status=status.HTTP_403_FORBIDDEN
            )
        obj = get_object_or_404(Calendrier, pk=pk)
        serializer = CalendrierSerializer(
            obj, data=request.data, partial=True, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if not request.user.is_staff:
            return Response(
                {'error': "Accès réservé aux administrateurs."},
                status=status.HTTP_403_FORBIDDEN
            )
        obj = get_object_or_404(Calendrier, pk=pk)
        titre = obj.titre
        obj.delete()
        return Response({'message': f'Calendrier "{titre}" supprimé.'}, status=status.HTTP_200_OK)


# ─── JourFerie Views ───────────────────────────────────────────────────────────

class JourFerieListAPIView(APIView):
    """
    GET  /api/calendrier/<cal_pk>/jours/   → jours fériés d'un calendrier
    POST /api/calendrier/<cal_pk>/jours/   → ajouter un jour (admin seulement)
    """
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, cal_pk):
        calendrier = get_object_or_404(Calendrier, pk=cal_pk)
        qs = calendrier.jours_feries.all().order_by('date')

        type_filter = request.query_params.get('type')
        if type_filter:
            qs = qs.filter(type_jour=type_filter)

        serializer = JourFerieSerializer(qs, many=True, context={'request': request})
        return Response({
            'count': qs.count(),
            'calendrier': {'id': calendrier.id, 'titre': calendrier.titre, 'annee': calendrier.annee},
            'jours_feries': serializer.data,
        })

    def post(self, request, cal_pk):
        if not request.user.is_staff:
            return Response(
                {'error': "Accès réservé aux administrateurs."},
                status=status.HTTP_403_FORBIDDEN
            )
        calendrier = get_object_or_404(Calendrier, pk=cal_pk)
        data = request.data.copy()
        data['calendrier'] = calendrier.id

        serializer = JourFerieSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            obj = serializer.save()
            return Response(
                JourFerieSerializer(obj, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JourFerieDetailAPIView(APIView):
    """
    GET    /api/calendrier/jours/<pk>/   → détail d'un jour
    PATCH  /api/calendrier/jours/<pk>/   → modifier (admin seulement)
    DELETE /api/calendrier/jours/<pk>/   → supprimer (admin seulement)
    """
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        obj = get_object_or_404(JourFerie, pk=pk)
        return Response(JourFerieSerializer(obj, context={'request': request}).data)

    def patch(self, request, pk):
        if not request.user.is_staff:
            return Response(
                {'error': "Accès réservé aux administrateurs."},
                status=status.HTTP_403_FORBIDDEN
            )
        obj = get_object_or_404(JourFerie, pk=pk)
        serializer = JourFerieSerializer(
            obj, data=request.data, partial=True, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if not request.user.is_staff:
            return Response(
                {'error': "Accès réservé aux administrateurs."},
                status=status.HTTP_403_FORBIDDEN
            )
        obj = get_object_or_404(JourFerie, pk=pk)
        titre = obj.titre
        obj.delete()
        return Response({'message': f'Jour "{titre}" supprimé.'}, status=status.HTTP_200_OK)


# ─── Vue globale : tous les jours fériés ──────────────────────────────────────

class TousJoursFeriesAPIView(APIView):
    """
    GET /api/calendrier/tous-jours/?annee=2025
    Retourne tous les jours fériés de tous les calendriers pour une année donnée.
    Utile pour le planning de présence.
    """
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        annee = request.query_params.get('annee', date.today().year)
        try:
            annee = int(annee)
        except ValueError:
            return Response({'error': "Année invalide."}, status=400)

        qs = JourFerie.objects.filter(
            date__year=annee
        ).select_related('calendrier').order_by('date')

        # Inclure aussi les jours récurrents d'autres années
        recurrents = JourFerie.objects.filter(
            est_recurrent=True
        ).exclude(date__year=annee).select_related('calendrier')

        dates_feries = set(qs.values_list('date', flat=True))

        data = JourFerieSerializer(qs, many=True, context={'request': request}).data

        return Response({
            'annee': annee,
            'count': len(data),
            'jours_feries': data,
        })
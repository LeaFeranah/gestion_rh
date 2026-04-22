from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.db.models import Min, Max, Q
from datetime import date, datetime
from .models import CheckInOut, UserInfo, Date, Evenement, HoraireSection, Anomalie
from .serializers import DateSerializer, HoraireSectionSerializer, EvenementSerializer, AnomalieSerializer
from .utils import decimal_to_time, analyser_presence, get_section_employe, corriger_pointages_automatique,get_active_badgenumbers
from .utils import get_active_userinfo_queryset
from .utils import decimal_to_time, analyser_presence, get_section_employe, \
    corriger_pointages_automatique, get_active_badgenumbers, \
    get_active_userinfo_queryset, calculer_heures_travaillees  
from .models import HoraireException
from .serializers import HoraireExceptionSerializer
from .utils import get_horaire_pour_date

import logging

logger = logging.getLogger(__name__)

class DateGenerationAPIView(APIView):
    """
    Générer les dates pour un mois donné ET créer les événements par défaut
    GET /api/presence/generer-dates/?annee=2024&mois=8
    """
    permission_classes = [AllowAny]

    def get(self, request):
        annee = int(request.query_params.get('annee', date.today().year))
        mois  = int(request.query_params.get('mois',  date.today().month))

        # ── 1. Générer les dates ────────────────────────────────────────────
        dates_crees = Date.generer_dates_mois(annee, mois)

        # ── 2. Récupérer les dates de la période (hors_periode=False) ───────
        mois_ref    = date(annee, mois, 1)
        dates_periode = list(
            Date.objects.filter(
                mois_reference=mois_ref,
                hors_periode=False
            ).values_list('date', flat=True)
        )

        #employes = list(UserInfo.objects.all())
        employes = list(get_active_userinfo_queryset())

        # ── 3. Créer les événements manquants en BULK (une seule requête) ───
        # Récupérer les paires (userid, date) déjà existantes
        existing = set(
            Evenement.objects.filter(date__in=dates_periode)
            .values_list('userid', 'date')
        )

        # Construire uniquement les objets manquants
        nouveaux = [
            Evenement(
                userid=employe.userid,
                date=date_jour,
                type_evenement='X',
                commentaire='Créé automatiquement'
            )
            for employe in employes
            for date_jour in dates_periode
            if (employe.userid, date_jour) not in existing
        ]

        evenements_crees = 0
        if nouveaux:
            created = Evenement.objects.bulk_create(nouveaux, ignore_conflicts=True)
            evenements_crees = len(created)

        # ── 4. Réponse ───────────────────────────────────────────────────────
        serializer = DateSerializer(dates_crees, many=True)

        mois_fr = [
            'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
        ]
        mois_precedent = mois - 1 if mois > 1 else 12

        return Response({
            "message":           f"Dates générées pour {mois_fr[mois-1]} {annee}",
            "periode":           f"21 {mois_fr[mois_precedent-1]} → 20 {mois_fr[mois-1]}",
            "count":             len(dates_crees),
            "evenements_crees":  evenements_crees,
            "dates":             serializer.data
        })


class DateListAPIView(APIView):
    """
    Lister toutes les dates avec leurs codes
    GET /api/presence/dates/?annee=2024&mois=8
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        annee = request.query_params.get('annee')
        mois = request.query_params.get('mois')
        
        if annee and mois:
            mois_ref = date(int(annee), int(mois), 1)
            dates = Date.objects.filter(mois_reference=mois_ref).order_by('date')
        else:
            dates = Date.objects.all().order_by('date')
        
        serializer = DateSerializer(dates, many=True)
        return Response(serializer.data)


# ========== PRÉSENCES SIMPLES (SANS CALCULS) ==========

class PresenceMoisAPIView(APIView):
    """
    Vue principale : Présences d'un mois avec codes dates
    GET /api/presence/mois/?annee=2024&mois=8
    """
    permission_classes = [AllowAny]

    def get(self, request):
        annee = request.query_params.get('annee')
        mois = request.query_params.get('mois')
        badgenumber = request.query_params.get('badgenumber')
        inclure_hors_periode = request.query_params.get('inclure_hors_periode', 'false').lower() == 'true'
        
        if not annee or not mois:
            return Response(
                {"error": "Les paramètres 'annee' et 'mois' sont obligatoires"}, 
                status=400
            )
        
        try:
            annee = int(annee)
            mois = int(mois)
        except ValueError:
            return Response({"error": "Année et mois doivent être des nombres"}, status=400)
        
        dates_mois = Date.get_dates_par_mois(annee, mois, inclure_hors_periode)
        dates_liste = list(dates_mois.values_list('date', flat=True))
        
        if not dates_liste:
            return Response({
                "message": f"Aucune date trouvée pour {mois}/{annee}. Générez d'abord les dates.",
                "dates_disponibles": []
            })
        
        pointages_query = CheckInOut.objects.filter(checktime__date__in=dates_liste)
        
        if badgenumber:
            pointages_query = pointages_query.filter(user__badgenumber=badgenumber)
        
        pointages = (
            pointages_query
            .select_related('user')
            .values('user__userid', 'user__badgenumber', 'user__name', 'checktime__date')
            .annotate(
                heure_entree=Min('checktime'),
                heure_sortie=Max('checktime')
            )
            .order_by('user__badgenumber', 'checktime__date')
        )
        
        dates_dict = {d.date: d for d in dates_mois}
        
        resultat = []
        
        for p in pointages:
            date_pointage = p["checktime__date"]
            date_obj = dates_dict.get(date_pointage)
            
            if date_obj:
                resultat.append({
                    "userid": p["user__userid"],
                    "badgenumber": p["user__badgenumber"],
                    "name": p["user__name"],
                    "date": date_pointage,
                    "code_date": date_obj.code_date,
                    "code_affichage": date_obj.code_affichage,
                    "hors_periode": date_obj.hors_periode,
                    "heure_entree": p["heure_entree"].time() if p["heure_entree"] else None,
                    "heure_sortie": p["heure_sortie"].time() if p["heure_sortie"] else None,
                    "evenement": "X"
                })
        
        mois_fr = [
            'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
        ]
        
        mois_precedent = mois - 1 if mois > 1 else 12
        
        return Response({
            "periode": {
                "mois": mois_fr[mois - 1],
                "annee": annee,
                "du": f"21 {mois_fr[mois_precedent - 1]}",
                "au": f"20 {mois_fr[mois - 1]}",
                "nombre_jours": len(dates_liste)
            },
            "presences": resultat,
            "total_presences": len(resultat)
        })


class PresenceMoisDetailAPIView(APIView):
    """
    Présence détaillée d'un employé pour un mois (avec TOUS les jours)
    GET /api/presence/mois/detail/?annee=2024&mois=8&badgenumber=123
    """
    permission_classes = [AllowAny]

    def get(self, request):
        annee = request.query_params.get('annee')
        mois = request.query_params.get('mois')
        badgenumber = request.query_params.get('badgenumber')
        inclure_hors_periode = request.query_params.get('inclure_hors_periode', 'false').lower() == 'true'
        
        if not annee or not mois or not badgenumber:
            return Response(
                {"error": "Les paramètres 'annee', 'mois' et 'badgenumber' sont obligatoires"}, 
                status=400
            )
        
        try:
            annee = int(annee)
            mois = int(mois)
        except ValueError:
            return Response({"error": "Année et mois doivent être des nombres"}, status=400)
        
        try:
            user_info = UserInfo.objects.get(badgenumber=badgenumber)
        except UserInfo.DoesNotExist:
            return Response(
                {"error": f"Utilisateur avec badgenumber={badgenumber} non trouvé"}, 
                status=404
            )
        
        dates_mois = Date.get_dates_par_mois(annee, mois, inclure_hors_periode)
        dates_liste = list(dates_mois.values_list('date', flat=True))
        
        pointages = (
            CheckInOut.objects
            .filter(user__badgenumber=badgenumber, checktime__date__in=dates_liste)
            .values('checktime__date')
            .annotate(
                heure_entree=Min('checktime'),
                heure_sortie=Max('checktime')
            )
        )
        
        pointages_dict = {p['checktime__date']: p for p in pointages}
        
        resultat = []
        
        for date_obj in dates_mois:
            pointage = pointages_dict.get(date_obj.date)
            
            resultat.append({
                "date": date_obj.date,
                "code_date": date_obj.code_date,
                "code_affichage": date_obj.code_affichage,
                "hors_periode": date_obj.hors_periode,
                "heure_entree": pointage['heure_entree'].time() if pointage and pointage['heure_entree'] else None,
                "heure_sortie": pointage['heure_sortie'].time() if pointage and pointage['heure_sortie'] else None,
                "present": pointage is not None,
                "evenement": "X" if pointage else "A"
            })
        
        mois_fr = [
            'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
        ]
        
        return Response({
            "employe": {
                "userid": user_info.userid,
                "badgenumber": user_info.badgenumber,
                "name": user_info.name
            },
            "periode": {
                "mois": mois_fr[mois - 1],
                "annee": annee
            },
            "presences": resultat,
            "statistiques": {
                "jours_total": len(resultat),
                "jours_presents": sum(1 for r in resultat if r['present']),
                "jours_absents": sum(1 for r in resultat if not r['present'])
            }
        })


class PresenceMoisRecapAPIView(APIView):
    """
    Récapitulatif des présences par employé pour un mois
    GET /api/presence/mois/recap/?annee=2024&mois=8
    """
    permission_classes = [AllowAny]

    def get(self, request):
        annee = request.query_params.get('annee')
        mois = request.query_params.get('mois')
        
        if not annee or not mois:
            return Response(
                {"error": "Les paramètres 'annee' et 'mois' sont obligatoires"}, 
                status=400
            )
        
        try:
            annee = int(annee)
            mois = int(mois)
        except ValueError:
            return Response({"error": "Année et mois doivent être des nombres"}, status=400)
        
        dates_mois = Date.get_dates_par_mois(annee, mois, inclure_hors_periode=False)
        dates_liste = list(dates_mois.values_list('date', flat=True))
        
        #employes = UserInfo.objects.all()
        employes = get_active_userinfo_queryset()
        
        resultat = []
        
        for employe in employes:
            jours_presents = (
                CheckInOut.objects
                .filter(user=employe, checktime__date__in=dates_liste)
                .values('checktime__date')
                .distinct()
                .count()
            )
            
            resultat.append({
                "userid": employe.userid,
                "badgenumber": employe.badgenumber,
                "name": employe.name,
                "jours_travailles": jours_presents,
                "jours_total": len(dates_liste),
                "taux_presence": round((jours_presents / len(dates_liste) * 100), 2) if dates_liste else 0
            })
        
        resultat.sort(key=lambda x: x['taux_presence'], reverse=True)
        
        mois_fr = [
            'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
        ]
        
        return Response({
            "periode": {
                "mois": mois_fr[mois - 1],
                "annee": annee,
                "jours_ouvrables": len(dates_liste)
            },
            "employes": resultat,
            "total_employes": len(resultat)
        })


class PresenceListAPIView(APIView):
    """
    API pour afficher toutes les présences de tous les utilisateurs
    GET /api/presence/
    """
    permission_classes = [AllowAny]

    def get(self, request):
        pointages = (
            CheckInOut.objects
            .select_related('user')
            .values('user__userid', 'user__badgenumber', 'user__name', 'checktime__date')
            .annotate(
                heure_entree=Min('checktime'),
                heure_sortie=Max('checktime')
            )
            .order_by('user__badgenumber', 'checktime__date')
        )

        resultat = []

        for p in pointages:
            resultat.append({
                "userid": p["user__userid"],
                "badgenumber": p["user__badgenumber"],
                "name": p["user__name"],
                "date": p["checktime__date"],
                "heure_entree": p["heure_entree"].time() if p["heure_entree"] else None,
                "heure_sortie": p["heure_sortie"].time() if p["heure_sortie"] else None,
                "evenement": "X"
            })

        return Response(resultat)


class PresenceAPIView(APIView):
    """
    API de gestion de présence par badgenumber
    GET /api/presence/123/
    """
    permission_classes = [AllowAny]

    def get(self, request, badgenumber):
        try:
            user_info = UserInfo.objects.get(badgenumber=badgenumber)
        except UserInfo.DoesNotExist:
            return Response(
                {"error": f"Utilisateur avec badgenumber={badgenumber} non trouvé"}, 
                status=404
            )

        pointages = (
            CheckInOut.objects
            .filter(user__badgenumber=badgenumber)
            .values('checktime__date')
            .annotate(
                heure_entree=Min('checktime'),
                heure_sortie=Max('checktime')
            )
            .order_by('checktime__date')
        )

        resultat = []

        for p in pointages:
            resultat.append({
                "userid": user_info.userid,
                "badgenumber": user_info.badgenumber,
                "name": user_info.name,
                "date": p["checktime__date"],
                "heure_entree": p["heure_entree"].time() if p["heure_entree"] else None,
                "heure_sortie": p["heure_sortie"].time() if p["heure_sortie"] else None,
                "evenement": "X"
            })

        return Response(resultat)


# ========== GESTION DES HORAIRES DE SECTION ==========

class HoraireSectionListAPIView(APIView):
    """
    Liste et création des horaires de section
    GET /api/presence/horaires-section/
    POST /api/presence/horaires-section/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Liste tous les horaires de section"""
        horaires = HoraireSection.objects.all()
        serializer = HoraireSectionSerializer(horaires, many=True)
        return Response({
            'count': horaires.count(),
            'horaires': serializer.data
        })
    
    def post(self, request):
        """Créer ou mettre à jour un horaire de section"""
        serializer = HoraireSectionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class HoraireSectionDetailAPIView(APIView):
    """
    Détail, modification et suppression d'un horaire de section
    GET /api/presence/horaires-section/{section}/
    PUT /api/presence/horaires-section/{section}/
    DELETE /api/presence/horaires-section/{section}/
    """
    permission_classes = [AllowAny]
    
    def get_object(self, section):
        try:
            return HoraireSection.objects.get(section=section)
        except HoraireSection.DoesNotExist:
            return None
    
    def get(self, request, section):
        """Récupérer un horaire de section"""
        horaire = self.get_object(section)
        if not horaire:
            return Response(
                {'error': f'Horaire pour la section {section} non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = HoraireSectionSerializer(horaire)
        return Response(serializer.data)
    
    def put(self, request, section):
        """Mettre à jour un horaire de section"""
        horaire = self.get_object(section)
        if not horaire:
            return Response(
                {'error': f'Horaire pour la section {section} non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = HoraireSectionSerializer(horaire, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, section):
        """Supprimer un horaire de section"""
        horaire = self.get_object(section)
        if not horaire:
            return Response(
                {'error': f'Horaire pour la section {section} non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        horaire.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    


class InitialiserHorairesAPIView(APIView):
    """
    Initialiser tous les horaires de section avec les données par défaut
    POST /api/presence/initialiser-horaires/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Initialise les horaires de toutes les sections"""
        count = HoraireSection.initialiser_horaires()
        return Response({
            'message': f'{count} horaires de section initialisés avec succès',
            'total': HoraireSection.objects.count()
        })


# ========== PRÉSENCES AVEC CALCULS ==========

class PresenceMoisCalculeeAPIView(APIView):
    """
    Présences avec calculs de retard et heures travaillées
    GET /api/presence/mois/calculee/?annee=2024&mois=8
    """
    permission_classes = [AllowAny]

    def get(self, request):
        annee = request.query_params.get('annee')
        mois = request.query_params.get('mois')
        badgenumber = request.query_params.get('badgenumber')
        inclure_hors_periode = request.query_params.get('inclure_hors_periode', 'false').lower() == 'true'
        
        if not annee or not mois:
            return Response(
                {"error": "Les paramètres 'annee' et 'mois' sont obligatoires"}, 
                status=400
            )
        
        try:
            annee = int(annee)
            mois = int(mois)
        except ValueError:
            return Response({"error": "Année et mois doivent être des nombres"}, status=400)
        
        dates_mois = Date.get_dates_par_mois(annee, mois, inclure_hors_periode)
        dates_liste = list(dates_mois.values_list('date', flat=True))
        
        if not dates_liste:
            return Response({
                "message": f"Aucune date trouvée pour {mois}/{annee}. Générez d'abord les dates.",
                "dates_disponibles": []
            })
        
        pointages_query = CheckInOut.objects.filter(checktime__date__in=dates_liste)
        
        if badgenumber:
            pointages_query = pointages_query.filter(user__badgenumber=badgenumber)
        
        pointages = (
            pointages_query
            .select_related('user')
            .values('user__userid', 'user__badgenumber', 'user__name', 'checktime__date')
            .annotate(
                heure_entree=Min('checktime'),
                heure_sortie=Max('checktime')
            )
            .order_by('user__badgenumber', 'checktime__date')
        )
        
        dates_dict = {d.date: d for d in dates_mois}
        
        resultat = []
        
        for p in pointages:
            date_pointage = p["checktime__date"]
            date_obj = dates_dict.get(date_pointage)
            
            if not date_obj:
                continue
            
            section = get_section_employe(p["user__badgenumber"])
            
            try:
                horaire = HoraireSection.objects.get(section=section)
            except HoraireSection.DoesNotExist:
                try:
                    horaire = HoraireSection.objects.get(section='ADMINISTRATION')
                except HoraireSection.DoesNotExist:
                    continue
            
            est_samedi = date_pointage.weekday() == 5
            heure_sortie_prevue_decimal = horaire.sortie_samedi if est_samedi else horaire.heure_sortie
            
            heure_entree_prevue = decimal_to_time(horaire.heure_entree)
            heure_sortie_prevue = decimal_to_time(heure_sortie_prevue_decimal)
            
            heure_entree_reelle = p["heure_entree"].time() if p["heure_entree"] else None
            heure_sortie_reelle = p["heure_sortie"].time() if p["heure_sortie"] else None
            
            analyse = analyser_presence(
                heure_entree_reelle,
                heure_sortie_reelle,
                heure_entree_prevue,
                heure_sortie_prevue,
                date_pointage
            )
            
            resultat.append({
                "userid": p["user__userid"],
                "badgenumber": p["user__badgenumber"],
                "name": p["user__name"],
                "section": section,
                "date": date_pointage,
                "code_date": date_obj.code_date,
                "code_affichage": date_obj.code_affichage,
                "hors_periode": date_obj.hors_periode,
                "est_samedi": est_samedi,
                
                "heure_entree_reelle": str(heure_entree_reelle) if heure_entree_reelle else None,
                "heure_sortie_reelle": str(heure_sortie_reelle) if heure_sortie_reelle else None,
                
                "heure_entree_prevue": str(heure_entree_prevue),
                "heure_sortie_prevue": str(heure_sortie_prevue),
                
                "heure_entree_comptabilisee": str(analyse['heure_entree_comptabilisee']) if analyse['heure_entree_comptabilisee'] else None,
                "heure_sortie_comptabilisee": str(analyse['heure_sortie_comptabilisee']) if analyse['heure_sortie_comptabilisee'] else None,
                
                "retard_minutes": analyse['retard_minutes'],
                "sortie_anticipee_minutes": analyse['sortie_anticipee_minutes'],
                "heures_travaillees": analyse['heures_travaillees'],
                "heures_prevues": analyse['heures_prevues'],
                "est_en_retard": analyse['est_en_retard'],
                "est_sorti_en_avance": analyse['est_sorti_en_avance'],
                
                "evenement": "X"
            })
        
        mois_fr = [
            'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
        ]
        
        mois_precedent = mois - 1 if mois > 1 else 12
        
        total_retard_minutes = sum(r['retard_minutes'] for r in resultat)
        total_sortie_anticipee_minutes = sum(r['sortie_anticipee_minutes'] for r in resultat)
        total_heures_travaillees = sum(r['heures_travaillees'] for r in resultat)
        total_heures_prevues = sum(r['heures_prevues'] for r in resultat)
        
        return Response({
            "periode": {
                "mois": mois_fr[mois - 1],
                "annee": annee,
                "du": f"21 {mois_fr[mois_precedent - 1]}",
                "au": f"20 {mois_fr[mois - 1]}",
                "nombre_jours": len(dates_liste)
            },
            "statistiques": {
                "total_presences": len(resultat),
                "total_retard_minutes": total_retard_minutes,
                "total_retard_heures": round(total_retard_minutes / 60, 2),
                "total_sortie_anticipee_minutes": total_sortie_anticipee_minutes,
                "total_sortie_anticipee_heures": round(total_sortie_anticipee_minutes / 60, 2),
                "total_heures_travaillees": round(total_heures_travaillees, 2),
                "total_heures_prevues": round(total_heures_prevues, 2),
                "nombre_retards": sum(1 for r in resultat if r['est_en_retard']),
                "nombre_sorties_anticipees": sum(1 for r in resultat if r['est_sorti_en_avance']),
            },
            "presences": resultat
        })
    

class PresenceMoisDetailCalculeeAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # 1. Paramètres
        annee = request.query_params.get('annee')
        mois = request.query_params.get('mois')
        badgenumber = request.query_params.get('badgenumber')
        section_filter = request.query_params.get('section', '').strip().upper()
        search = request.query_params.get('q', '').strip()
        inclure_hors_periode = request.query_params.get('inclure_hors_periode', 'false').lower() == 'true'

        try:
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 50))
            if page < 1:
                page = 1
            if page_size < 1:
                page_size = 50
            if page_size > 200:
                page_size = 200
        except ValueError:
            return Response({"error": "Les paramètres page et page_size doivent être des nombres"}, status=400)

        if not annee or not mois:
            return Response({"error": "Les paramètres 'annee' et 'mois' sont obligatoires"}, status=400)

        try:
            annee = int(annee)
            mois = int(mois)
        except ValueError:
            return Response({"error": "Année et mois doivent être des nombres"}, status=400)

        mois_fr = [
            'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
        ]
        mois_precedent = mois - 1 if mois > 1 else 12

        # 2. Dates de la période
        dates_mois = Date.get_dates_par_mois(annee, mois, inclure_hors_periode)
        if not dates_mois.exists():
            return Response({
                "message": f"Aucune date trouvée pour {mois}/{annee}. Générez d'abord les dates.",
                "dates_disponibles": []
            })

        dates_mois = list(dates_mois)
        dates_liste = [d.date for d in dates_mois]
        periode_data = {
            "mois": mois_fr[mois - 1],
            "annee": annee,
            "du": f"21 {mois_fr[mois_precedent - 1]}",
            "au": f"20 {mois_fr[mois - 1]}",
            "nombre_jours": len(dates_liste)
        }

        from .models import UserSection

        # 3. Section -> liste des userids
        userids_section = None
        if section_filter:
            # Récupérer la map section effective pour trouver les userids correspondants
            from .utils import build_user_section_map
            user_section_map_full = build_user_section_map()  # {userid: section_effective}
            userids_section = {
                uid for uid, sec in user_section_map_full.items()
                if sec.upper() == section_filter
            }

            if not userids_section:
                return Response({
                    "periode": periode_data,
                    "statistiques": {},
                    "pagination": {
                        "page": page,
                        "page_size": page_size,
                        "total_employees": 0,
                        "total_pages": 0,
                        "has_next": False,
                        "has_previous": False,
                    },
                    "presences": []
                })

        # 4. Base : tous les employés actifs
        users_qs = get_active_userinfo_queryset()

        if badgenumber:
            users_qs = users_qs.filter(badgenumber=badgenumber)

        if userids_section is not None:
            users_qs = users_qs.filter(userid__in=userids_section)

        if search:
            users_qs = users_qs.filter(
                Q(name__icontains=search) |
                Q(badgenumber__icontains=search)
            )

        users_qs = users_qs.order_by('badgenumber', 'userid')
        total_employees = users_qs.count()

        if total_employees == 0:
            return Response({
                "periode": periode_data,
                "statistiques": {},
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_employees": 0,
                    "total_pages": 0,
                    "has_next": False,
                    "has_previous": False,
                },
                "presences": []
            })

        total_pages = (total_employees + page_size - 1) // page_size
        if page > total_pages:
            page = total_pages

        start = (page - 1) * page_size
        end = start + page_size
        users_page = list(users_qs[start:end])
        user_ids_page = {u.userid for u in users_page}

        # 5. Pointages pour la page courante
        pointages_qs = CheckInOut.objects.filter(
            checktime__date__in=dates_liste,
            user_id__in=user_ids_page
        )
        pointages_data = pointages_qs.values('user_id', 'checktime', 'checktype')

        pointages_par_jour = {}
        for p in pointages_data:
            key = (p['user_id'], str(p['checktime'].date()))
            pointages_par_jour.setdefault(key, []).append({
                'checktime': p['checktime'],
                'checktype': p['checktype']
            })

        # 6. Anomalies corrigées pour la page courante
        anomalies_qs = Anomalie.objects.filter(
            date__in=dates_liste,
            etat='ok',
            userid__in=user_ids_page
        )
        anomalies_map = {}
        for a in anomalies_qs:
            key = (a.userid, str(a.date))
            anomalies_map[key] = {
                'heure_entree': a.heure_reelle_entree,
                'heure_sortie': a.heure_reelle_sortie,
                'heure_rectifiee_entree': a.heure_rectifiee_entree,
                'heure_rectifiee_sortie': a.heure_rectifiee_sortie,
                'heure_brute_entree': a.heure_brute_entree,
                'heure_brute_sortie': a.heure_brute_sortie,
                'section': a.section,
                'synchronise_le': a.synchronise_le,
            }

        # 7. Événements pour la page courante
        evenements_qs = Evenement.objects.filter(
            date__in=dates_liste,
            userid__in=user_ids_page
        )
        evenements_map = {}
        for e in evenements_qs:
            key = (e.userid, str(e.date))
            evenements_map[key] = {
                'type': e.type_evenement,
                'commentaire': e.commentaire,
            }

        # 8. Map section utilisateur pour la page courante
        # Utiliser build_user_section_map filtré sur la page
        from .utils import build_user_section_map, RESPONSABLE_VARIANTS
        user_section_map_full = build_user_section_map()
        user_section_map = {
            uid: sec for uid, sec in user_section_map_full.items()
            if uid in user_ids_page
        }

        # Fallback UserSection pour ceux non couverts
        missing_ids = user_ids_page - set(user_section_map.keys())
        if missing_ids:
            for us in UserSection.objects.select_related('section').filter(userid__in=missing_ids):
                if us.section_id is not None:
                    user_section_map[us.userid] = us.section.nom_section

        # 9. Horaires
        sections_page = set(user_section_map.values()) | {'ADMINISTRATION'}
        horaires_dict = {
            h.section: h
            for h in HoraireSection.objects.filter(section__in=sections_page)
        }
        # Fallback si section non trouvée dans horaires
        horaire_default = horaires_dict.get('ADMINISTRATION')
        if not horaire_default:
            horaire_default = HoraireSection.objects.first()

        # 10. Construction du résultat
        resultat = []

        for user in users_page:
            section = user_section_map.get(user.userid, 'ADMINISTRATION')
            horaire = horaires_dict.get(section, horaire_default)

            if horaire is None:
                continue

            for date_obj in dates_mois:
                date_str = str(date_obj.date)
                key = (user.userid, date_str)

                evenement_data = evenements_map.get(key)
                anomalie_corrigee = anomalies_map.get(key)
                pointages_du_jour = pointages_par_jour.get(key, [])

                present = bool(pointages_du_jour) or (anomalie_corrigee is not None)

                est_samedi = date_obj.date.weekday() == 5
                est_vendredi = date_obj.date.weekday() == 4
                est_jour_paiement = date_obj.est_jour_paiement

                # Utiliser la fonction qui prend en compte les exceptions d'horaire
                heure_entree_prevue, heure_sortie_prevue = get_horaire_pour_date(
                    horaire,
                    date_obj.date,
                    est_jour_paiement,
                    section=section   # 'section' est défini plus haut dans la boucle employé
                )

                if anomalie_corrigee:
                    heure_brute_entree = anomalie_corrigee['heure_brute_entree']
                    heure_brute_sortie = anomalie_corrigee['heure_brute_sortie']
                    heure_rectifiee_entree = anomalie_corrigee['heure_rectifiee_entree']
                    heure_rectifiee_sortie = anomalie_corrigee['heure_rectifiee_sortie']
                    synchronise_le = anomalie_corrigee['synchronise_le']
                    if anomalie_corrigee.get('section'):
                        section_affichee = anomalie_corrigee['section']
                    else:
                        section_affichee = section
                else:
                    section_affichee = section
                    if pointages_du_jour:
                        tries = sorted(pointages_du_jour, key=lambda p: p['checktime'])
                        heure_brute_entree = tries[0]['checktime'].time()
                        heure_brute_sortie = tries[-1]['checktime'].time() if len(tries) > 1 else None
                        heure_rectifiee_entree = heure_brute_entree
                        heure_rectifiee_sortie = heure_brute_sortie
                    else:
                        heure_brute_entree = None
                        heure_brute_sortie = None
                        heure_rectifiee_entree = None
                        heure_rectifiee_sortie = None
                    synchronise_le = None

                if anomalie_corrigee is not None:
                    # Correction manuelle : on affiche exactement ce qui a été saisi
                    analyse = {
                        'heure_entree_comptabilisee': heure_rectifiee_entree,
                        'heure_sortie_comptabilisee': heure_rectifiee_sortie,
                        'retard_minutes': 0,
                        'sortie_anticipee_minutes': 0,
                        'heures_travaillees': float(
                            calculer_heures_travaillees(heure_rectifiee_entree, heure_rectifiee_sortie)
                        ) if heure_rectifiee_entree and heure_rectifiee_sortie else 0.0,
                        'heures_prevues': float(
                            calculer_heures_travaillees(heure_entree_prevue, heure_sortie_prevue)
                        ),
                        'est_en_retard': False,
                        'est_sorti_en_avance': False,
                        'difference_heures': 0.0,
                    }
                else:
                    # Calcul automatique avec les règles habituelles
                    analyse = analyser_presence(
                        heure_rectifiee_entree,
                        heure_rectifiee_sortie,
                        heure_entree_prevue,
                        heure_sortie_prevue,
                        date_obj.date
                    )


                resultat.append({
                    "userid": user.userid,
                    "badgenumber": user.badgenumber,
                    "name": user.name,
                    "section": section_affichee,
                    "date": date_str,
                    "code_date": date_obj.code_date,
                    "code_affichage": date_obj.code_affichage,
                    "hors_periode": date_obj.hors_periode,
                    "est_samedi": est_samedi,
                    "est_vendredi": est_vendredi,
                    "est_jour_paiement": est_jour_paiement,
                    "est_anomalie_corrigee": anomalie_corrigee is not None,
                    "synchronise_le": str(synchronise_le) if synchronise_le else None,
                    "present": present,
                    "heure_brute_entree": str(heure_brute_entree) if heure_brute_entree else None,
                    "heure_brute_sortie": str(heure_brute_sortie) if heure_brute_sortie else None,
                    "heure_entree_rectifiee": str(heure_rectifiee_entree) if heure_rectifiee_entree else None,
                    "heure_sortie_rectifiee": str(heure_rectifiee_sortie) if heure_rectifiee_sortie else None,
                    "heure_entree_prevue": str(heure_entree_prevue),
                    "heure_sortie_prevue": str(heure_sortie_prevue),
                    "type_sortie_prevue": (
                        "vendredi_paiement" if est_jour_paiement and est_vendredi else
                        "samedi_paiement" if est_jour_paiement and est_samedi else
                        "samedi_normal" if est_samedi else
                        "normal"
                    ),
                    "heure_entree_comptabilisee": str(analyse['heure_entree_comptabilisee']) if analyse['heure_entree_comptabilisee'] else None,
                    "heure_sortie_comptabilisee": str(analyse['heure_sortie_comptabilisee']) if analyse['heure_sortie_comptabilisee'] else None,
                    "retard_minutes": analyse['retard_minutes'],
                    "sortie_anticipee_minutes": analyse['sortie_anticipee_minutes'],
                    "heures_travaillees": analyse['heures_travaillees'],
                    "heures_prevues": analyse['heures_prevues'],
                    "est_en_retard": analyse['est_en_retard'],
                    "est_sorti_en_avance": analyse['est_sorti_en_avance'],
                    "difference_heures": analyse['difference_heures'],
                    "evenement": evenement_data['type'] if evenement_data else 'X',
                    "evenement_commentaire": evenement_data['commentaire'] if evenement_data else "",
                    "has_special_event": bool(evenement_data and evenement_data['type'] != 'X'),
                })

        resultat.sort(key=lambda x: (x['badgenumber'], x['date']))

        # 11. Statistiques
        total_retard_minutes = sum(r['retard_minutes'] for r in resultat)
        total_sortie_anticipee_minutes = sum(r['sortie_anticipee_minutes'] for r in resultat)
        total_heures_travaillees = sum(r['heures_travaillees'] for r in resultat)
        total_heures_prevues = sum(r['heures_prevues'] for r in resultat)
        total_anomalies_corrigees = sum(1 for r in resultat if r['est_anomalie_corrigee'])
        total_with_special_events = sum(1 for r in resultat if r['has_special_event'])

        stats = {
            "total_presences": len(resultat),
            "total_retard_minutes": total_retard_minutes,
            "total_retard_heures": round(total_retard_minutes / 60, 2),
            "total_sortie_anticipee_minutes": total_sortie_anticipee_minutes,
            "total_sortie_anticipee_heures": round(total_sortie_anticipee_minutes / 60, 2),
            "total_heures_travaillees": round(total_heures_travaillees, 2),
            "total_heures_prevues": round(total_heures_prevues, 2),
            "nombre_retards": sum(1 for r in resultat if r['est_en_retard']),
            "nombre_sorties_anticipees": sum(1 for r in resultat if r['est_sorti_en_avance']),
            "nombre_jours_paiement": sum(1 for r in resultat if r['est_jour_paiement']),
            "nombre_anomalies_corrigees": total_anomalies_corrigees,
            "nombre_evenements_speciaux": total_with_special_events,
        }

        return Response({
            "periode": periode_data,
            "statistiques": stats,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_employees": total_employees,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            },
            "presences": resultat
        })


# ========== GESTION DES ÉVÉNEMENTS ==========

class EvenementListAPIView(APIView):
    """
    Liste et création d'événements
    GET /api/presence/evenements/?annee=2024&mois=8
    POST /api/presence/evenements/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Liste tous les événements (avec filtres optionnels)"""
        evenements = Evenement.objects.all()
        
        annee = request.query_params.get('annee')
        mois = request.query_params.get('mois')
        badgenumber = request.query_params.get('badgenumber')
        
        if annee and mois:
            mois_ref = date(int(annee), int(mois), 1)
            dates_mois = Date.objects.filter(mois_reference=mois_ref).values_list('date', flat=True)
            evenements = evenements.filter(date__in=dates_mois)
        
        if badgenumber:
            evenements = evenements.filter(userid__in=UserInfo.objects.filter(badgenumber=badgenumber).values_list('userid', flat=True))
        
        evenements = evenements.order_by('-date')
        serializer = EvenementSerializer(evenements, many=True)
        
        return Response({
            'count': evenements.count(),
            'evenements': serializer.data
        })
    
    def post(self, request):
        """Créer un événement"""
        serializer = EvenementSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EvenementDetailAPIView(APIView):
    """
    Détail, modification et suppression d'un événement
    GET /api/presence/evenements/{id}/
    PUT /api/presence/evenements/{id}/
    DELETE /api/presence/evenements/{id}/
    """
    permission_classes = [AllowAny]
    
    def get_object(self, pk):
        try:
            return Evenement.objects.get(pk=pk)
        except Evenement.DoesNotExist:
            return None
    
    def get(self, request, pk):
        """Récupérer un événement"""
        evenement = self.get_object(pk)
        if not evenement:
            return Response(
                {'error': 'Événement non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = EvenementSerializer(evenement)
        return Response(serializer.data)
    
    def put(self, request, pk):
        """Mettre à jour un événement"""
        evenement = self.get_object(pk)
        if not evenement:
            return Response(
                {'error': 'Événement non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = EvenementSerializer(evenement, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """Supprimer un événement"""
        evenement = self.get_object(pk)
        if not evenement:
            return Response(
                {'error': 'Événement non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        evenement.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EvenementByUserDateAPIView(APIView):
    """
    Gérer un événement par user et date
    GET /api/presence/evenements/user/{userid}/date/{date}/
    POST /api/presence/evenements/user/{userid}/date/{date}/
    DELETE /api/presence/evenements/user/{userid}/date/{date}/
    """
    permission_classes = [AllowAny]
    
    def get(self, request, userid, date_str):
        """Récupérer l'événement pour un user et une date"""
        try:
            evenement = Evenement.objects.get(userid=userid, date=date_str)
            serializer = EvenementSerializer(evenement)
            return Response(serializer.data)
        except Evenement.DoesNotExist:
            return Response({
                'evenement': None,
                'type_evenement': 'X',
                'message': 'Aucun événement enregistré'
            })
    
    def post(self, request, userid, date_str):
        """Créer ou mettre à jour un événement"""
        data = request.data.copy()
        data['userid'] = userid
        data['date'] = date_str
        
        try:
            # UTILISER update_or_create POUR GARANTIR LA PERSISTANCE
            evenement, created = Evenement.objects.update_or_create(
                userid=userid,
                date=date_str,
                defaults={
                    'type_evenement': data.get('type_evenement', 'X'),
                    'commentaire': data.get('commentaire', '')
                }
            )
            
            serializer = EvenementSerializer(evenement)
            
            return Response({
                'success': True,
                'created': created,
                'evenement': serializer.data,
                'message': 'Événement créé' if created else 'Événement mis à jour'
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, userid, date_str):
        """Supprimer un événement (retour à 'X' par défaut)"""
        try:
            # AU LIEU DE SUPPRIMER, RÉINITIALISER À 'X'
            evenement, created = Evenement.objects.update_or_create(
                userid=userid,
                date=date_str,
                defaults={
                    'type_evenement': 'X',
                    'commentaire': ''
                }
            )
            
            return Response({
                'success': True,
                'message': 'Événement réinitialisé à "X"'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class TypesEvenementAPIView(APIView):
    """
    Liste les types d'événements disponibles
    GET /api/presence/types-evenements/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Liste tous les types d'événements"""
        types = [
            {'code': code, 'libelle': libelle}
            for code, libelle in Evenement.TYPES_EVENEMENT
        ]
        return Response({'types_evenements': types})



class AnomalieListAPIView(APIView):
    """
    Liste des anomalies avec filtres
    GET /api/presence/anomalies/?annee=2024&mois=8&section=BRODERIE&etat=pas_entree
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Liste toutes les anomalies avec filtres optionnels"""
        anomalies = Anomalie.objects.all()
        
        annee = request.query_params.get('annee')
        mois = request.query_params.get('mois')
        section = request.query_params.get('section')
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        etat = request.query_params.get('etat')
        
        if annee and mois:
            mois_ref = date(int(annee), int(mois), 1)
            dates_mois = Date.objects.filter(
                mois_reference=mois_ref,
                hors_periode=False
            ).values_list('date', flat=True)
            anomalies = anomalies.filter(date__in=dates_mois)
        
        if date_debut:
            anomalies = anomalies.filter(date__gte=date_debut)
        
        if date_fin:
            anomalies = anomalies.filter(date__lte=date_fin)
        
        if section:
            anomalies = anomalies.filter(section=section)
        
        if etat:
            anomalies = anomalies.filter(etat=etat)
        
        anomalies = anomalies.select_related().order_by('-date', 'section', 'userid')
        serializer = AnomalieSerializer(anomalies, many=True)
        
        # Statistiques
        stats = {
            'total': anomalies.count(),
            'corrigees': anomalies.filter(etat='ok').count(),
            'non_corrigees': anomalies.exclude(etat='ok').count(),
            'par_etat': {}
        }
        
        for etat_code, etat_libelle in Anomalie.ETATS_ANOMALIE:
            count = anomalies.filter(etat=etat_code).count()
            if count > 0:
                stats['par_etat'][etat_code] = {
                    'libelle': etat_libelle,
                    'count': count
                }
        
        return Response({
            'count': anomalies.count(),
            'statistiques': stats,
            'anomalies': serializer.data
        })


class AnomalieDetailAPIView(APIView):
    """
    Détail et modification d'une anomalie
    GET /api/presence/anomalies/{id}/
    PUT /api/presence/anomalies/{id}/
    PATCH /api/presence/anomalies/{id}/
    """
    permission_classes = [AllowAny]
    
    def get_object(self, pk):
        try:
            return Anomalie.objects.get(pk=pk)
        except Anomalie.DoesNotExist:
            return None
    
    def get(self, request, pk):
        """Récupérer une anomalie"""
        anomalie = self.get_object(pk)
        if not anomalie:
            return Response(
                {'error': 'Anomalie non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = AnomalieSerializer(anomalie)
        return Response(serializer.data)
    
    def put(self, request, pk):
        """Mettre à jour complètement une anomalie"""
        return self._update_anomalie(request, pk, partial=False)
    
    def patch(self, request, pk):
        """Mettre à jour partiellement une anomalie"""
        return self._update_anomalie(request, pk, partial=True)
    
    def _update_anomalie(self, request, pk, partial=False):
        """
        Logique de mise à jour d'une anomalie
        """
        anomalie = self.get_object(pk)
        if not anomalie:
            return Response(
                {'error': 'Anomalie non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = AnomalieSerializer(anomalie, data=request.data, partial=partial)
        if serializer.is_valid():
            anomalie_updated = serializer.save()
            
            # Vérifier si l'anomalie est maintenant OK
            # if anomalie_updated.etat == 'ok':
            #     # Optionnel : synchroniser avec CheckInOut si nécessaire
            #     self._synchroniser_avec_checkinout(anomalie_updated)
            
            return Response(AnomalieSerializer(anomalie_updated).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _synchroniser_avec_checkinout(self, anomalie):
        """
        Synchronise l'anomalie corrigée avec la table CheckInOut
        """
        try:
            user = UserInfo.objects.get(userid=anomalie.userid)
            
            # Formater les heures sans secondes
            from datetime import datetime, time
            
            def format_time_for_checkinout(time_obj):
                """Formate le temps pour CheckInOut (sans secondes)"""
                if time_obj:
                    return time(time_obj.hour, time_obj.minute, 0)
                return None
            
            # Supprimer les anciens pointages du jour
            CheckInOut.objects.filter(
                user=user,
                checktime__date=anomalie.date
            ).delete()
            
            # Créer les nouveaux pointages avec les heures corrigées (sans secondes)
            if anomalie.heure_reelle_entree:
                CheckInOut.objects.create(
                    user=user,
                    checktime=datetime.combine(
                        anomalie.date, 
                        format_time_for_checkinout(anomalie.heure_reelle_entree)
                    ),
                    checktype='O'  # O = entrée
                )
            
            if anomalie.heure_reelle_sortie:
                CheckInOut.objects.create(
                    user=user,
                    checktime=datetime.combine(
                        anomalie.date, 
                        format_time_for_checkinout(anomalie.heure_reelle_sortie)
                    ),
                    checktype='I'  # I = sortie
                )
            
            logger.info(f"Synchronisation OK pour {user.name} le {anomalie.date}")
            return True
        except Exception as e:
            logger.error(f"Erreur synchronisation CheckInOut: {e}")
            return False



class HoraireExceptionListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = HoraireException.objects.all()
        date_filter = request.query_params.get('date')
        if date_filter:
            qs = qs.filter(date=date_filter)
        return Response(HoraireExceptionSerializer(qs, many=True).data)

    def post(self, request):
        serializer = HoraireExceptionSerializer(data=request.data)
        if serializer.is_valid():
            exception = serializer.save()
            # ← NOUVEAU : mettre à jour heure_reelle des anomalies existantes
            self._refresh_anomalies_pour_date(exception)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _refresh_anomalies_pour_date(self, exception):
        """
        Après création d'une exception d'horaire, met à jour heure_reelle_entree
        et heure_reelle_sortie dans les anomalies déjà enregistrées pour cette date.
        heure_rectifiee n'est pas touchée (corrections manuelles conservées).
        """
        from .utils import get_horaire_pour_date
        try:
            date_jour = exception.date
            try:
                date_obj = Date.objects.get(date=date_jour)
                est_paiement = date_obj.est_jour_paiement
            except Date.DoesNotExist:
                return

            anomalies_qs = Anomalie.objects.filter(date=date_jour)
            if exception.section:
                anomalies_qs = anomalies_qs.filter(section=exception.section)

            horaires_cache = {h.section: h for h in HoraireSection.objects.all()}
            horaire_default = horaires_cache.get('ADMINISTRATION')

            to_update = []
            for anomalie in anomalies_qs:
                section = anomalie.section or 'ADMINISTRATION'
                horaire = horaires_cache.get(section, horaire_default)
                if not horaire:
                    continue
                nouvelle_entree, nouvelle_sortie = get_horaire_pour_date(
                    horaire, date_jour, est_paiement, section=section
                )
                anomalie.heure_reelle_entree = nouvelle_entree
                anomalie.heure_reelle_sortie = nouvelle_sortie
                to_update.append(anomalie)

            if to_update:
                Anomalie.objects.bulk_update(
                    to_update, ['heure_reelle_entree', 'heure_reelle_sortie']
                )
                logger.info(
                    f"HoraireException {exception.date}: "
                    f"{len(to_update)} anomalie(s) rafraîchie(s)"
                )
        except Exception as e:
            logger.warning(f"_refresh_anomalies_pour_date: {e}")




class HoraireExceptionDetailAPIView(APIView):
    """
    GET    /api/presence/horaire-exceptions/<id>/
    PATCH  /api/presence/horaire-exceptions/<id>/
    DELETE /api/presence/horaire-exceptions/<id>/
    """
    permission_classes = [AllowAny]

    def get_object(self, pk):
        try:
            return HoraireException.objects.get(pk=pk)
        except HoraireException.DoesNotExist:
            return None

    def get(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'Non trouvé'}, status=404)
        return Response(HoraireExceptionSerializer(obj).data)

    def patch(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'Non trouvé'}, status=404)
        serializer = HoraireExceptionSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'Non trouvé'}, status=404)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SupprimerPresencesJourAPIView(APIView):
    """
    Supprime les présences d'une journée donnée (par section ou toutes sections).
    - Heures brutes (CheckInOut) : conservées
    - Heures rectifiées : vidées (None)
    - Événements : réinitialisés à 'X'
    DELETE /api/presence/supprimer-jour/
    Body: { "date": "2025-04-13", "motif": "Jour férié", "section": "ADMINISTRATION" }
    """
    permission_classes = [AllowAny]

    def delete(self, request):
        date_str = request.data.get('date')
        motif    = request.data.get('motif', '')
        section  = request.data.get('section', None)

        if not date_str:
            return Response({"error": "Le paramètre 'date' est obligatoire"}, status=400)
        try:
            date_jour = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": "Format YYYY-MM-DD attendu"}, status=400)

        # ── Tous les pointages du jour ───────────────────────────────────────
        pointages_jour = (
            CheckInOut.objects
            .filter(checktime__date=date_jour)
            .values('user_id', 'checktime', 'checktype')
            .order_by('user_id', 'checktime')
        )

        pointages_par_user = {}
        for p in pointages_jour:
            pointages_par_user.setdefault(p['user_id'], []).append(p)

        if not pointages_par_user:
            return Response({
                "success": True,
                "date": date_str,
                "message": "Aucun pointage trouvé pour cette date."
            })

        # ── Map section ──────────────────────────────────────────────────────
        from .utils import build_user_section_map
        from .models import UserSection, Section as SectionModel

        user_section_map = build_user_section_map()

        # ── Filtrer par section si précisée ──────────────────────────────────
        if section:
            sec_obj = SectionModel.objects.filter(nom_section=section).first()
            userids_usersection = set()
            if sec_obj:
                userids_usersection = set(
                    UserSection.objects.filter(section=sec_obj)
                    .values_list('userid', flat=True)
                )

            userids_cibles = {
                uid for uid in pointages_par_user
                if user_section_map.get(uid) == section or uid in userids_usersection
            }
        else:
            userids_cibles = set(pointages_par_user.keys())

        if not userids_cibles:
            return Response({
                "success": True,
                "date": date_str,
                "section": section or "",
                "message": f"Aucun employé trouvé pour la section '{section}'."
            })

        # ── Infos date ───────────────────────────────────────────────────────
        try:
            date_obj     = Date.objects.get(date=date_jour)
            code_date    = date_obj.code_date
            est_paiement = date_obj.est_jour_paiement
        except Date.DoesNotExist:
            code_date    = ''
            est_paiement = False

        horaires_dict   = {h.section: h for h in HoraireSection.objects.all()}
        horaire_default = horaires_dict.get('ADMINISTRATION')

        from .utils import get_horaire_pour_date
        from datetime import datetime as dt

        # ── Boucle : créer anomalie avec heures brutes / rectifiées vides ────
        count = 0
        for userid in userids_cibles:
            pts = pointages_par_user.get(userid, [])
            if not pts:
                continue

            entrees = [p for p in pts if p['checktype'].upper() == 'O']
            sorties = [p for p in pts if p['checktype'].upper() == 'I']

            heure_brute_entree = (
                entrees[0]['checktime'].time() if entrees
                else pts[0]['checktime'].time()
            )
            heure_brute_sortie = (
                sorties[-1]['checktime'].time() if sorties
                else (pts[-1]['checktime'].time() if len(pts) > 1 else None)
            )

            sec     = user_section_map.get(userid, section or 'ADMINISTRATION')
            horaire = horaires_dict.get(sec, horaire_default)

            heure_reelle_entree = heure_reelle_sortie = None
            if horaire:
                heure_reelle_entree, heure_reelle_sortie = get_horaire_pour_date(
                    horaire, date_jour, est_paiement, section=sec
                )

            # Créer/mettre à jour l'anomalie
            Anomalie.objects.update_or_create(
                userid=userid,
                date=date_jour,
                defaults={
                    'section':                sec,
                    'code_date':              code_date,
                    'heure_brute_entree':     heure_brute_entree,
                    'heure_brute_sortie':     heure_brute_sortie,
                    'heure_reelle_entree':    heure_reelle_entree,
                    'heure_reelle_sortie':    heure_reelle_sortie,
                    'heure_rectifiee_entree': None,
                    'heure_rectifiee_sortie': None,
                    'commentaire':            motif or 'Supprimé',
                }
            )

            # Forcer etat='ok' + rectifiées=None via update() direct (bypass save())
            Anomalie.objects.filter(userid=userid, date=date_jour).update(
                heure_rectifiee_entree=None,
                heure_rectifiee_sortie=None,
                etat='ok',
                synchronise_le=dt.now(),
            )
            count += 1

        # ── Réinitialiser les événements à 'X' ──────────────────────────────
        Evenement.objects.filter(
            userid__in=userids_cibles,
            date=date_jour
        ).update(
            type_evenement='X',
            commentaire=''
        )

        section_label = section if section else "toutes les sections"

        logger.info(
            f"Suppression présences {date_jour} [{section_label}] – "
            f"{count} employés. Motif: {motif}"
        )

        return Response({
            "success": True,
            "date": date_str,
            "section": section or "",
            "motif": motif,
            "nb_presences_supprimees": count,
            "message": (
                f"{count} présence(s) et événement(s) supprimés pour le {date_str} "
                f"[{section_label}]. Heures brutes conservées."
            )
        })

class DetecterAnomaliesAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        annee = request.data.get('annee')
        mois = request.data.get('mois')
        if not annee or not mois:
            return Response({"error": "annee et mois obligatoires"}, status=400)
        try:
            annee, mois = int(annee), int(mois)
        except ValueError:
            return Response({"error": "Nombres attendus"}, status=400)

        dates_mois = Date.get_dates_par_mois(annee, mois, inclure_hors_periode=False)
        dates_liste = list(dates_mois.values_list('date', flat=True))
        dates_map = {d.date: d for d in dates_mois}

        if not dates_liste:
            return Response({"error": "Générez d'abord les dates"}, status=400)

        # ── 1. Charger les données statiques UNE SEULE FOIS ────────────────
        from .utils import build_user_section_map, decimal_to_time, analyser_pointages_jour

        user_section_map = build_user_section_map()  # {userid: section_nom}
        horaires_dict    = {h.section: h for h in HoraireSection.objects.all()}
        horaire_default  = horaires_dict.get('ADMINISTRATION')

        # ── 2. Charger TOUS les pointages de la période EN UNE requête ─────
        from django.db.models import Prefetch
        tous_pointages = (
            CheckInOut.objects
            .filter(checktime__date__in=dates_liste)
            .values('user_id', 'checktime', 'checktype')
            .order_by('user_id', 'checktime')
        )

        # Regrouper en mémoire : {(userid, date): [pointages]}
        pointages_map = {}
        for p in tous_pointages:
            key = (p['user_id'], p['checktime'].date())
            pointages_map.setdefault(key, []).append(p)

        # ── 3. Seuls les employés qui ont pointé ──────────────────────────
        userids_actifs = {uid for (uid, _) in pointages_map.keys()}
        employes_map = {
            u.userid: u
            for u in UserInfo.objects.filter(userid__in=userids_actifs)
        }

        # ── 4. Nettoyer les anomalies obsolètes (employés sans pointage) ──
        Anomalie.objects.filter(
            date__in=dates_liste
        ).exclude(userid__in=userids_actifs).delete()

        # ── 5. Boucle principale sans aucune requête DB dedans ─────────────
        to_create = []
        to_update = []
        to_delete_ids = []
        existing = {
            (a.userid, a.date): a
            for a in Anomalie.objects.filter(date__in=dates_liste)
        }

        for (userid, date_jour), pointages_raw in pointages_map.items():
            employe = employes_map.get(userid)
            if not employe:
                continue

            date_obj = dates_map.get(date_jour)
            if not date_obj:
                continue

            section = user_section_map.get(userid, 'ADMINISTRATION')
            horaire = horaires_dict.get(section, horaire_default)
            if horaire is None:
                continue

            est_samedi   = date_jour.weekday() == 5
            est_vendredi = date_jour.weekday() == 4
            est_paiement = date_obj.est_jour_paiement


            from .utils import get_horaire_pour_date
            heure_reelle_entree, heure_reelle_sortie = get_horaire_pour_date(
                horaire, date_jour, est_paiement, section=section
            )

            # Convertir les dicts en objets compatibles avec analyser_pointages_jour
            class FakePointage:
                def __init__(self, d):
                    self.checktime = d['checktime']
                    self.checktype = d['checktype']

            pointages_list = [FakePointage(p) for p in pointages_raw]
            tries = sorted(pointages_list, key=lambda p: p.checktime)

            entrees_brutes = [p for p in tries if p.checktype.upper() == 'O']
            sorties_brutes = [p for p in tries if p.checktype.upper() == 'I']
            heure_brute_entree = entrees_brutes[0].checktime.time() if entrees_brutes else None
            heure_brute_sortie = sorties_brutes[-1].checktime.time() if sorties_brutes else None

            h_entree, h_sortie, type_anomalie, liste_bruts = analyser_pointages_jour(
                pointages_list, heure_reelle_entree, heure_reelle_sortie, seuil_minutes=30
            )

            if type_anomalie == 'multiples_pointages':
                etat = 'multiples_pointages'
                h_rect_entree = h_rect_sortie = None
            elif type_anomalie == 'pas_entree' or h_entree is None:
                etat = 'pas_entree'
                h_rect_entree, h_rect_sortie = None, h_sortie
            elif type_anomalie == 'pas_sortie' or h_sortie is None:
                etat = 'pas_sortie'
                h_rect_entree, h_rect_sortie = h_entree, None
            else:
                etat = 'ok'
                h_rect_entree, h_rect_sortie = h_entree, h_sortie

            # Les anomalies OK sont supprimées
            key = (userid, date_jour)
            if etat == 'ok':
                if key in existing:
                    to_delete_ids.append(existing[key].pk)
                continue

            fields = dict(
                section=section,
                code_date=date_obj.code_date,
                heure_brute_entree=heure_brute_entree,
                heure_brute_sortie=heure_brute_sortie,
                heure_reelle_entree=heure_reelle_entree,
                heure_reelle_sortie=heure_reelle_sortie,
                heure_rectifiee_entree=h_rect_entree,
                heure_rectifiee_sortie=h_rect_sortie,
                pointages_bruts_json=liste_bruts,
                etat=etat,
                commentaire='',
            )

            if key in existing:
                obj = existing[key]
                for attr, val in fields.items():
                    setattr(obj, attr, val)
                to_update.append(obj)
            else:
                to_create.append(Anomalie(userid=userid, date=date_jour, **fields))

        # ── 6. Opérations bulk ─────────────────────────────────────────────
        if to_delete_ids:
            Anomalie.objects.filter(pk__in=to_delete_ids).delete()

        if to_create:
            Anomalie.objects.bulk_create(to_create, ignore_conflicts=True)

        if to_update:
            Anomalie.objects.bulk_update(to_update, fields=[
                'section', 'code_date',
                'heure_brute_entree', 'heure_brute_sortie',
                'heure_reelle_entree', 'heure_reelle_sortie',
                'heure_rectifiee_entree', 'heure_rectifiee_sortie',
                'pointages_bruts_json', 'etat', 'commentaire',
            ])

        total = len(to_create) + len(to_update)
        anomalies = Anomalie.objects.filter(date__in=dates_liste)

        return Response({
            'message': f'{total} anomalies traitées pour {mois}/{annee}',
            'total': total,
            'periode': {'annee': annee, 'mois': mois, 'jours_analyses': len(dates_liste)},
            'statistiques': {
                'par_etat': {
                    code: {'libelle': lib, 'count': anomalies.filter(etat=code).count()}
                    for code, lib in Anomalie.ETATS_ANOMALIE
                    if anomalies.filter(etat=code).exists()
                },
                'total_corrigees': 0,
                'total_non_corrigees': total,
            }
        })

class AnomalieParSectionAPIView(APIView):
    """
    Anomalies groupées par section et par date
    GET /api/presence/anomalies/par-section/?annee=2024&mois=8
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        annee = request.query_params.get('annee')
        mois = request.query_params.get('mois')
        
        if not annee or not mois:
            return Response(
                {"error": "Les paramètres 'annee' et 'mois' sont obligatoires"},
                status=400
            )
        
        mois_ref = date(int(annee), int(mois), 1)
        dates_mois = Date.objects.filter(
            mois_reference=mois_ref,
            hors_periode=False
        ).values_list('date', flat=True)
        
        anomalies = Anomalie.objects.filter(
            date__in=dates_mois
        ).order_by('section', 'date', 'userid')
        
        # Grouper par section
        par_section = {}
        for anomalie in anomalies:
            section = anomalie.section or 'SANS SECTION'
            if section not in par_section:
                par_section[section] = {
                    'section': section,
                    'total': 0,
                    'corrigees': 0,
                    'non_corrigees': 0,
                    'par_etat': {},
                    'par_date': {}
                }
            
            date_str = str(anomalie.date)
            if date_str not in par_section[section]['par_date']:
                par_section[section]['par_date'][date_str] = []
            
            par_section[section]['par_date'][date_str].append(
                AnomalieSerializer(anomalie).data
            )
            par_section[section]['total'] += 1
            
            if anomalie.etat == 'ok':
                par_section[section]['corrigees'] += 1
            else:
                par_section[section]['non_corrigees'] += 1
            
            # Compter par état
            etat_display = anomalie.get_etat_display()
            if etat_display not in par_section[section]['par_etat']:
                par_section[section]['par_etat'][etat_display] = 0
            par_section[section]['par_etat'][etat_display] += 1
        
        return Response({
            'periode': {'annee': int(annee), 'mois': int(mois)},
            'total_sections': len(par_section),
            'sections': list(par_section.values())
        })


class CorrigerAnomalieAPIView(APIView):
    """
    Correction rapide d'une anomalie avec règles automatiques
    POST /api/presence/anomalies/{id}/corriger/
    Body: {
        "action": "inverser" | "reel_vide" | "copier_brut" | "manuel",
        "heure_rectifiee_entree": "08:00:00",  # optionnel pour action "manuel"
        "heure_rectifiee_sortie": "17:00:00"   # optionnel pour action "manuel"
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request, pk):
        try:
            anomalie = Anomalie.objects.get(pk=pk)
        except Anomalie.DoesNotExist:
            return Response(
                {'error': 'Anomalie non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        action = request.data.get('action')
        
        if action == 'correction_auto':
            # Correction automatique pour inversion
            if anomalie.corriger_inversion_automatique():
                return Response({
                    'message': 'Correction automatique appliquée',
                    'anomalie': AnomalieSerializer(anomalie).data
                })
            else:
                return Response({
                    'error': 'Correction automatique impossible'
                }, status=400)
        
        elif action == 'egaliser_reel_rectifie':
            # Égaliser les heures réelles et rectifiées
            anomalie.heure_rectifiee_entree = anomalie.heure_reelle_entree
            anomalie.heure_rectifiee_sortie = anomalie.heure_reelle_sortie
            anomalie.save()
            
            return Response({
                'message': 'Heures égalisées avec succès',
                'anomalie': AnomalieSerializer(anomalie).data
            })
    

# views.py - Ajouter cette vue
class AnomaliesCorrigeesAPIView(APIView):
    """
    Récupérer les anomalies corrigées pour un mois
    GET /api/presence/anomalies-corrigees/?annee=2024&mois=8
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        annee = request.query_params.get('annee')
        mois = request.query_params.get('mois')
        
        if not annee or not mois:
            return Response(
                {"error": "Les paramètres 'annee' et 'mois' sont obligatoires"},
                status=400
            )
        
        try:
            mois_ref = date(int(annee), int(mois), 1)
            dates_mois = Date.objects.filter(
                mois_reference=mois_ref,
                hors_periode=False
            ).values_list('date', flat=True)
            
            anomalies = Anomalie.objects.filter(
                date__in=dates_mois,
                etat='ok'
            ).order_by('section', 'date', 'userid')
            
            anomalies_data = []
            for anomalie in anomalies:
                anomalies_data.append({
                    'id': anomalie.id,
                    'userid': anomalie.userid,
                    'date': anomalie.date,
                    'section': anomalie.section,
                    'code_date': anomalie.code_date,
                    'heure_reelle_entree': anomalie.heure_reelle_entree,
                    'heure_reelle_sortie': anomalie.heure_reelle_sortie,
                    'heure_rectifiee_entree': anomalie.heure_rectifiee_entree,
                    'heure_rectifiee_sortie': anomalie.heure_rectifiee_sortie,
                    'est_corrigee': anomalie.est_corrigee,
                    'synchronise_le': anomalie.synchronise_le
                })
            
            return Response({
                'count': anomalies.count(),
                'anomalies': anomalies_data
            })
            
        except Exception as e:
            logger.error(f"Erreur récupération anomalies corrigées: {e}")
            return Response(
                {"error": str(e)},
                status=500
            )
        

class ModifierHeuresManuellementAPIView(APIView):
    """
    API pour modifier manuellement les heures d'un employé pour une date donnée.
    Les heures brutes (pointages d'origine) sont conservées et ne sont jamais modifiées.
    Seules les heures rectifiées sont enregistrées.
    POST /api/presence/modifier-heures/
    Body:
    {
        "userid": 123,
        "date": "2024-08-15",
        "heure_entree": "08:00:00",   // ou "08:00" (HH:MM)
        "heure_sortie": "17:30:00",
        "commentaire": "Oubli de pointage"
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            userid = request.data.get('userid')
            date_str = request.data.get('date')
            heure_entree_str = request.data.get('heure_entree')
            heure_sortie_str = request.data.get('heure_sortie')
            commentaire = request.data.get('commentaire', '')

            # Validation des paramètres obligatoires
            if not userid or not date_str:
                return Response(
                    {"error": "Les paramètres 'userid' et 'date' sont obligatoires"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Conversion de la date
            try:
                date_jour = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "Format de date invalide. Utilisez YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Au moins une heure doit être fournie
            if not heure_entree_str and not heure_sortie_str:
                return Response(
                    {"error": "Au moins une heure (entrée ou sortie) doit être fournie"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Fonction utilitaire pour convertir une chaîne HH:MM ou HH:MM:SS en objet time
            def str_to_time(t_str):
                if not t_str:
                    return None
                try:
                    return datetime.strptime(t_str, "%H:%M:%S").time()
                except ValueError:
                    try:
                        return datetime.strptime(t_str, "%H:%M").time()
                    except ValueError:
                        return None

            heure_entree = str_to_time(heure_entree_str)
            heure_sortie = str_to_time(heure_sortie_str)

            # Récupération de l'utilisateur
            try:
                user = UserInfo.objects.get(userid=userid)
            except UserInfo.DoesNotExist:
                return Response(
                    {"error": f"Utilisateur {userid} non trouvé"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Détermination de la section
            section = get_section_employe(user.badgenumber)

            # Récupération de l'horaire de la section
            try:
                horaire = HoraireSection.objects.get(section=section)
            except HoraireSection.DoesNotExist:
                horaire = HoraireSection.objects.get(section='ADMINISTRATION')

            # Récupération de l'objet Date pour obtenir code_date et est_jour_paiement
            try:
                date_obj = Date.objects.get(date=date_jour)
                code_date = date_obj.code_date
                est_jour_paiement = date_obj.est_jour_paiement
            except Date.DoesNotExist:
                # Génération à la volée si la date n'existe pas (normalement déjà générée)
                from calendar import monthrange
                if date_jour.month == 1:
                    annee_prec = date_jour.year - 1
                    mois_prec = 12
                else:
                    annee_prec = date_jour.year
                    mois_prec = date_jour.month - 1
                debut_periode = datetime(annee_prec, mois_prec, 21).date()
                lundi_debut = Date.get_lundi_precedent(debut_periode)
                code_date = Date.calculer_code_date(date_jour, lundi_debut)
                est_jour_paiement = False

            # Détermination des heures prévues (heure_reelle) selon la date
            est_samedi = date_jour.weekday() == 5
            est_vendredi = date_jour.weekday() == 4

            heure_reelle_entree = decimal_to_time(horaire.heure_entree)

            if est_jour_paiement and est_vendredi:
                heure_reelle_sortie = decimal_to_time(horaire.sortie_vendredi_paiement)
            elif est_jour_paiement and est_samedi:
                heure_reelle_sortie = decimal_to_time(horaire.sortie_samedi_paiement)
            elif est_samedi:
                heure_reelle_sortie = decimal_to_time(horaire.sortie_samedi)
            else:
                heure_reelle_sortie = decimal_to_time(horaire.heure_sortie)

            pointages_bruts = list(
                CheckInOut.objects.filter(
                    user=user,
                    checktime__date=date_jour
                ).order_by('checktime')
            )

            heure_brute_entree = None
            heure_brute_sortie = None
            if pointages_bruts:
                heure_brute_entree = pointages_bruts[0].checktime.time()
                if len(pointages_bruts) > 1:
                    heure_brute_sortie = pointages_bruts[-1].checktime.time()  # ✅ fonctionne sur une liste



            # --- CRÉATION / MISE À JOUR DE L'ANOMALIE ---
            # On conserve systématiquement les heures brutes, on ne les écrase jamais.
            # Les heures rectifiées sont celles saisies par l'utilisateur.
            anomalie, created = Anomalie.objects.update_or_create(
                userid=userid,
                date=date_jour,
                defaults={
                    'section': section,
                    'code_date': code_date,
                    'heure_brute_entree': heure_brute_entree,   
                    'heure_brute_sortie': heure_brute_sortie,
                    'heure_reelle_entree': heure_reelle_entree,
                    'heure_reelle_sortie': heure_reelle_sortie,
                    'heure_rectifiee_entree': heure_entree,
                    'heure_rectifiee_sortie': heure_sortie,
                    'commentaire': commentaire,
                }
            )

            # L'état est automatiquement recalculé par la méthode save() du modèle Anomalie
            # On rafraîchit l'instance pour obtenir l'état à jour
            anomalie.refresh_from_db()

            # SUPPRESSION DE TOUTE SYNCHRONISATION AVEC CheckInOut
            # Les pointages bruts restent intacts dans la table d'origine.
            # Aucune création / suppression / modification n'est effectuée sur CheckInOut.

            serializer = AnomalieSerializer(anomalie)
            return Response({
                "success": True,
                "message": "Heures modifiées avec succès (heures brutes conservées)",
                "anomalie": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Erreur dans ModifierHeuresManuellementAPIView: {e}", exc_info=True)
            return Response(
                {"error": f"Erreur interne : {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SupprimerHeuresManuellementAPIView(APIView):
    """
    API pour supprimer les heures modifiées manuellement
    DELETE /api/presence/supprimer-heures/
    """
    permission_classes = [AllowAny]
    
    def delete(self, request):
        """
        Supprime les modifications manuelles et rétablit les pointages bruts
        
        Body:
        {
            "userid": 123,
            "date": "2024-08-15"
        }
        """
        try:
            userid = request.data.get('userid')
            date_str = request.data.get('date')
            
            if not userid or not date_str:
                return Response(
                    {"error": "Les paramètres 'userid' et 'date' sont obligatoires"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Convertir la date
            try:
                date_jour = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "Format de date invalide. Utilisez YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Supprimer l'anomalie
            try:
                anomalie = Anomalie.objects.get(userid=userid, date=date_jour)
                
                # Si c'était une anomalie corrigée, supprimer les pointages synchronisés
                if anomalie.etat == 'ok':
                    user = UserInfo.objects.get(userid=userid)
                    
                    # Supprimer tous les pointages du jour
                    CheckInOut.objects.filter(
                        user=user,
                        checktime__date=date_jour
                    ).delete()
                    
                    # Recréer les pointages bruts s'ils existaient
                    if anomalie.heure_brute_entree:
                        CheckInOut.objects.create(
                            user=user,
                            checktime=datetime.combine(date_jour, anomalie.heure_brute_entree),
                            checktype='O'
                        )
                    
                    if anomalie.heure_brute_sortie:
                        CheckInOut.objects.create(
                            user=user,
                            checktime=datetime.combine(date_jour, anomalie.heure_brute_sortie),
                            checktype='I'
                        )
                
                anomalie.delete()
                
                return Response({
                    "success": True,
                    "message": "Modifications supprimées et pointages rétablis"
                })
                
            except Anomalie.DoesNotExist:
                return Response(
                    {"error": "Aucune modification manuelle trouvée pour cette date"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression des heures: {e}")
            return Response(
                {"error": f"Erreur: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetHeuresJourAPIView(APIView):
    """
    API pour récupérer toutes les heures disponibles pour un jour donné
    GET /api/presence/heures-jour/?userid=123&date=2024-08-15
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        userid = request.query_params.get('userid')
        date_str = request.query_params.get('date')
        
        if not userid or not date_str:
            return Response(
                {"error": "Les paramètres 'userid' et 'date' sont obligatoires"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            date_jour = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Format de date invalide. Utilisez YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Récupérer l'utilisateur
            user = UserInfo.objects.get(userid=userid)
            
            # Récupérer la section
            from .utils import get_section_employe
            section = get_section_employe(user.badgenumber)
            
            # Récupérer l'horaire de section
            try:
                horaire = HoraireSection.objects.get(section=section)
            except HoraireSection.DoesNotExist:
                horaire = HoraireSection.objects.get(section='ADMINISTRATION')
            
            # Récupérer la date avec ses propriétés
            try:
                date_obj = Date.objects.get(date=date_jour)
                est_jour_paiement = date_obj.est_jour_paiement
                code_date = date_obj.code_affichage
            except Date.DoesNotExist:
                est_jour_paiement = False
                code_date = ''
            
            # Déterminer l'heure de sortie prévue
            est_samedi = date_jour.weekday() == 5
            est_vendredi = date_jour.weekday() == 4
            
            heure_entree_prevue = decimal_to_time(horaire.heure_entree)
            
            if est_jour_paiement:
                if est_vendredi:
                    heure_sortie_prevue = decimal_to_time(horaire.sortie_vendredi_paiement)
                else:
                    heure_sortie_prevue = decimal_to_time(horaire.sortie_samedi_paiement)
            elif est_samedi:
                heure_sortie_prevue = decimal_to_time(horaire.sortie_samedi)
            else:
                heure_sortie_prevue = decimal_to_time(horaire.heure_sortie)
            
            # Récupérer les pointages bruts
            pointages = CheckInOut.objects.filter(
                user=user,
                checktime__date=date_jour
            ).order_by('checktime')
            
            heure_brute_entree = None
            heure_brute_sortie = None
            
            if pointages.exists():
                entree = pointages.filter(checktype='O').first()
                sortie = pointages.filter(checktype='I').last()
                
                if entree:
                    heure_brute_entree = entree.checktime.time()
                if sortie:
                    heure_brute_sortie = sortie.checktime.time()
            
            # Récupérer l'anomalie si elle existe
            anomalie = None
            try:
                anomalie = Anomalie.objects.get(userid=userid, date=date_jour)
            except Anomalie.DoesNotExist:
                pass
            
            # Récupérer l'événement
            evenement = None
            try:
                evenement_obj = Evenement.objects.get(userid=userid, date=date_jour)
                evenement = {
                    'type': evenement_obj.type_evenement,
                    'commentaire': evenement_obj.commentaire
                }
            except Evenement.DoesNotExist:
                evenement = {'type': 'X', 'commentaire': ''}
            
            return Response({
                'user': {
                    'userid': user.userid,
                    'badgenumber': user.badgenumber,
                    'name': user.name,
                    'section': section
                },
                'date': date_str,
                'code_date': code_date,
                'est_jour_paiement': est_jour_paiement,
                'est_samedi': est_samedi,
                'est_vendredi': est_vendredi,
                'horaires_prevu': {
                    'entree': str(heure_entree_prevue) if heure_entree_prevue else None,
                    'sortie': str(heure_sortie_prevue) if heure_sortie_prevue else None
                },
                'pointages_bruts': {
                    'entree': str(heure_brute_entree) if heure_brute_entree else None,
                    'sortie': str(heure_brute_sortie) if heure_brute_sortie else None
                },
                'anomalie': AnomalieSerializer(anomalie).data if anomalie else None,
                'evenement': evenement
            })
            
        except UserInfo.DoesNotExist:
            return Response(
                {"error": f"Utilisateur {userid} non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des heures: {e}")
            return Response(
                {"error": f"Erreur: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class SearchEmployeesAPIView(APIView):
    """
    Recherche d'employés par badge ou nom
    GET /api/presence/search-employees/?q=recherche
    """
    permission_classes = [AllowAny]

    def get(self, request):
        query = request.query_params.get('q', '').strip()

        if not query or len(query) < 2:
            return Response({
                'employees': [],
                'message': 'Saisissez au moins 2 caractères'
            })

        active_badges = set(get_active_badgenumbers())

        employees = UserInfo.objects.filter(
            badgenumber__in=active_badges
        ).filter(
            Q(badgenumber__icontains=query) |
            Q(name__icontains=query)
        ).order_by('badgenumber')[:20]

        results = []
        for emp in employees:
            section = get_section_employe(emp.badgenumber)
            results.append({
                'userid': emp.userid,
                'badgenumber': emp.badgenumber,
                'name': emp.name,
                'section': section
            })

        return Response({
            'employees': results,
            'count': len(results)
        })


class SectionListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        from .models import UserSection, UserInfo
        from personnel.models import InformationPersonnelle, InformationProfessionnelle
        from django.db.models import Q
        from .utils import build_user_section_map

        search = request.query_params.get('search', '').strip()

        # Construire la map userid→section_effective (actifs uniquement, RESPONSABLE remplacés)
        user_section_map = build_user_section_map()  # {userid: section_effective}

        # Compter les employés par section_effective
        section_counts = {}
        for section in user_section_map.values():
            if section:
                section_counts[section] = section_counts.get(section, 0) + 1

        # Filtrer par recherche si demandé
        data = []
        for nom_section, nb in sorted(section_counts.items()):
            if search and search.upper() not in nom_section.upper():
                continue
            if nb > 0:
                data.append({
                    'section_id': nom_section,   # on utilise le nom comme id
                    'nom_section': nom_section,
                    'nb_employes': nb,
                })

        return Response({
            'count': len(data),
            'sections': data
        })



class SectionEmployesAPIView(APIView):
    """
    Employés d'une section donnée
    GET /api/presence/sections/<section_id>/employes/
    """
    permission_classes = [AllowAny]

    def get(self, request, section_id):
        from .models import Section, UserSection
        try:
            section = Section.objects.get(pk=section_id)
        except Section.DoesNotExist:
            return Response({'error': 'Section non trouvée'}, status=404)

        employes = UserSection.objects.filter(section=section).select_related('user')
        data = [
            {'userid': us.user.userid, 'badgenumber': us.user.badgenumber, 'name': us.user.name}
            for us in employes
        ]
        return Response({'section': section.nom_section, 'count': len(data), 'employes': data})


class HeuresTravailAPIView(APIView):
    """
    Calcul des heures travaillées (HT) et supplémentaires (HS) selon les règles :
    - Pour les jours normaux (lundi→vendredi) selon le type d'événement (X, HA, OS, PS)
    - Pour le samedi : règle unique pour X, HA, OS, PS ; 0 pour les autres événements
    Les heures sont calculées à partir des pointages bruts ou des anomalies corrigées.
    """
    permission_classes = [AllowAny]

    @staticmethod
    def _calculer_ht_et_hs(entree, sortie, est_samedi, type_evenement):
        """
        Retourne (heures_travaillees, heures_supp) au format décimal.
        Formules Excel fournies :
        - Jour normal :
            * X : HS = SI(durée<8; durée-8; durée-0.5-8) ; HT = durée - (0.5 si durée>=8)
            * HA : HS = SI(durée<8; durée-7; durée-0.5-7) ; HT = durée - (0.5 si durée>=8)
            * OS ou PS : HS = durée - 8.5 ; HT = durée - (0.5 si durée>=8.5)
            * autre : HS = 0 ; HT = durée
        - Samedi (pour X, HA, OS, PS) :
            * HS = SI(durée<6; durée; durée-0.5)
            * HT = durée - (0.5 si durée>=6)
            * autre événement : HS = 0 ; HT = durée
        """
        if not entree or not sortie:
            return 0.0, 0.0

        # Durée en heures décimales
        ref = date.today()
        delta_minutes = (datetime.combine(ref, sortie) - datetime.combine(ref, entree)).total_seconds() / 60
        duree_heures = delta_minutes / 60.0
        if duree_heures <= 0:
            return 0.0, 0.0

        if est_samedi:
            # Règle samedi : s'applique à X, HA, OS, PS
            if type_evenement in ('X', 'HA', 'OS', 'PS'):
                if duree_heures < 6:
                    hs = duree_heures
                else:
                    hs = duree_heures - 0.5
                pause = 0.5 if duree_heures >= 6 else 0
                ht = duree_heures - pause
            else:
                hs = 0.0
                ht = duree_heures   # pas de pause pour les autres
            return max(0, ht), max(0, hs)

        # Jour normal (lundi à vendredi)
        if type_evenement == 'X':
            if duree_heures < 8:
                hs = duree_heures - 8
                pause = 0
            else:
                hs = duree_heures - 0.5 - 8
                pause = 0.5
            ht = duree_heures - pause
        elif type_evenement == 'HA':
            if duree_heures < 8:
                hs = duree_heures - 7
                pause = 0
            else:
                hs = duree_heures - 0.5 - 7
                pause = 0.5
            ht = duree_heures - pause
        elif type_evenement in ('OS', 'PS'):
            hs = duree_heures - 8.5
            pause = 0.5 if duree_heures >= 8.5 else 0
            ht = duree_heures - pause
        else:
            hs = 0.0
            ht = duree_heures

        return max(0, ht), max(0, hs)

    def get(self, request):
        try:
            annee     = int(request.query_params.get('annee', date.today().year))
            mois      = int(request.query_params.get('mois',  date.today().month))
            page      = max(1, int(request.query_params.get('page', 1)))
            page_size = min(200, max(1, int(request.query_params.get('page_size', 50))))
        except ValueError:
            return Response({"error": "Paramètres invalides"}, status=400)

        section_filter = request.query_params.get('section', '').strip().upper()
        q              = request.query_params.get('q', '').strip()

        from .utils import (
            build_user_section_map,
            analyser_pointages_jour,
            get_horaire_pour_date,
            get_active_userinfo_queryset,
        )

        # ── Dates de la période ──────────────────────────────────────────────
        dates_mois_qs = Date.get_dates_par_mois(annee, mois, inclure_hors_periode=False)
        if not dates_mois_qs.exists():
            return Response({"error": "Générez d'abord les dates pour ce mois."}, status=400)

        dates_mois  = list(dates_mois_qs)
        dates_liste = [d.date for d in dates_mois]

        # Regroupement par semaine
        semaines_dates: dict = {}
        for d in dates_mois:
            s = d.code_date[0] if d.code_date else '1'
            semaines_dates.setdefault(s, []).append(d)
        semaine_nums = sorted(semaines_dates.keys())

        # ── Employés actifs ──────────────────────────────────────────────────
        user_section_map = build_user_section_map()

        users_qs = get_active_userinfo_queryset().order_by('badgenumber')

        if section_filter:
            ids_sec  = {uid for uid, sec in user_section_map.items()
                        if sec.upper() == section_filter}
            users_qs = users_qs.filter(userid__in=ids_sec)

        if q:
            users_qs = users_qs.filter(
                Q(name__icontains=q) | Q(badgenumber__icontains=q)
            )

        total_employees = users_qs.count()
        if total_employees == 0:
            return self._empty_response(annee, mois, semaine_nums, page, page_size)

        total_pages = (total_employees + page_size - 1) // page_size
        page        = min(page, total_pages)
        users_page  = list(users_qs[(page - 1) * page_size: page * page_size])
        user_ids    = {u.userid for u in users_page}

        # ── Pré-chargements ──────────────────────────────────────────────────
        # Anomalies corrigées (état 'ok')
        anomalies_map: dict = {}
        for a in Anomalie.objects.filter(
            date__in=dates_liste, etat='ok', userid__in=user_ids
        ):
            anomalies_map[(a.userid, a.date)] = a

        # Pointages bruts
        pointages_map: dict = {}
        for p in (
            CheckInOut.objects
            .filter(checktime__date__in=dates_liste, user_id__in=user_ids)
            .values('user_id', 'checktime', 'checktype')
        ):
            pointages_map.setdefault(
                (p['user_id'], p['checktime'].date()), []
            ).append(p)

        # Événements (type d'absence)
        evenements_map: dict = {}
        for ev in Evenement.objects.filter(
            userid__in=user_ids,
            date__in=dates_liste
        ).values('userid', 'date', 'type_evenement'):
            evenements_map[(ev['userid'], ev['date'])] = ev['type_evenement']

        # Horaires des sections
        horaires_dict   = {h.section: h for h in HoraireSection.objects.all()}
        horaire_default = horaires_dict.get('ADMINISTRATION')

        # Classe légère pour analyser_pointages_jour
        class FP:
            __slots__ = ('checktime', 'checktype')
            def __init__(self, d):
                self.checktime = d['checktime']
                self.checktype = d['checktype']

        # ── Calcul par employé ───────────────────────────────────────────────
        results = []

        for user in users_page:
            section_emp = user_section_map.get(user.userid, 'ADMINISTRATION')
            horaire     = horaires_dict.get(section_emp, horaire_default)

            # Initialisation des accumulateurs par semaine
            par_semaine = {
                s: {'ht': 0.0, 'hs': 0.0, 'jours': 0}
                for s in semaine_nums
            }
            # Détails journaliers
            details_jours = []

            total_ht = 0.0
            total_hs = 0.0

            for date_obj in dates_mois:
                date_jour = date_obj.date
                semaine   = date_obj.code_date[0] if date_obj.code_date else '1'
                key       = (user.userid, date_jour)

                entree = sortie = None
                type_evenement = evenements_map.get(key, 'X')

                # 1. Anomalie corrigée en priorité (heures rectifiées)
                anomalie = anomalies_map.get(key)
                if (anomalie
                        and anomalie.heure_rectifiee_entree
                        and anomalie.heure_rectifiee_sortie):
                    entree = anomalie.heure_rectifiee_entree
                    sortie = anomalie.heure_rectifiee_sortie

                # 2. Sinon pointages bruts analysés
                elif key in pointages_map and horaire:
                    h_e, h_s = get_horaire_pour_date(
                        horaire, date_jour,
                        date_obj.est_jour_paiement,
                        section=section_emp,
                    )
                    pts = [FP(p) for p in pointages_map[key]]
                    he, hs, type_a, _ = analyser_pointages_jour(
                        pts, h_e, h_s, seuil_minutes=30
                    )
                    if type_a is None and he and hs:
                        entree, sortie = he, hs

                if entree and sortie:
                    est_samedi = (date_jour.weekday() == 5)
                    ht, hs = self._calculer_ht_et_hs(
                        entree, sortie, est_samedi, type_evenement
                    )
                    par_semaine[semaine]['ht'] += ht
                    par_semaine[semaine]['hs'] += hs
                    par_semaine[semaine]['jours'] += 1
                    total_ht += ht
                    total_hs += hs

                    details_jours.append({
                        'date': date_jour.isoformat(),
                        'code_date': date_obj.code_affichage,
                        'ht': round(ht, 2),
                        'hs': round(hs, 2),
                        'type_evenement': type_evenement,
                    })
                else:
                    details_jours.append({
                        'date': date_jour.isoformat(),
                        'code_date': date_obj.code_affichage,
                        'ht': 0,
                        'hs': 0,
                        'type_evenement': type_evenement,
                    })

            # Arrondir à 2 décimales
            for s in semaine_nums:
                par_semaine[s]['ht'] = round(par_semaine[s]['ht'], 2)
                par_semaine[s]['hs'] = round(par_semaine[s]['hs'], 2)

            results.append({
                'userid':        user.userid,
                'badgenumber':   user.badgenumber,
                'name':          user.name,
                'section':       section_emp,
                'par_semaine':   par_semaine,
                'details_jours': details_jours,
                'total_ht':      round(total_ht, 2),
                'total_hs':      round(total_hs, 2),
                'total_jours':   sum(par_semaine[s]['jours'] for s in semaine_nums),
            })

        mois_fr        = ['Janvier','Février','Mars','Avril','Mai','Juin',
                          'Juillet','Août','Septembre','Octobre','Novembre','Décembre']
        mois_precedent = mois - 1 if mois > 1 else 12

        return Response({
            'periode': {
                'mois':  mois_fr[mois - 1],
                'annee': annee,
                'du':    f"21 {mois_fr[mois_precedent - 1]}",
                'au':    f"20 {mois_fr[mois - 1]}",
            },
            'semaines':   semaine_nums,
            'pagination': {
                'page':            page,
                'page_size':       page_size,
                'total_employees': total_employees,
                'total_pages':     total_pages,
                'has_next':        page < total_pages,
                'has_previous':    page > 1,
            },
            'employes': results,
        })

    @staticmethod
    def _empty_response(annee, mois, semaine_nums, page, page_size):
        mois_fr = ['Janvier','Février','Mars','Avril','Mai','Juin',
                'Juillet','Août','Septembre','Octobre','Novembre','Décembre']
        mois_precedent = mois - 1 if mois > 1 else 12  # ← ajouter cette ligne
        return Response({
            'periode': {
                'mois':  mois_fr[mois - 1],
                'annee': annee,
                'du':    f"21 {mois_fr[mois_precedent - 1]}",  # ← était ''
                'au':    f"20 {mois_fr[mois - 1]}",             # ← était ''
            },
            'semaines': semaine_nums,
            'pagination': {
                'page':            page,
                'page_size':       page_size,
                'total_employees': 0,
                'total_pages':     0,
                'has_next':        False,
                'has_previous':    False,
            },
            'employes': [],
        })


class IndemniteRepasAPIView(APIView):
    """
    Calcul du nombre de jours d'indemnité repas par employé pour un mois.
    Un jour est indemnisé si les heures travaillées (HT) >= 3.83 heures.
    """
    permission_classes = [AllowAny]

    @staticmethod
    def _heures_travaillees(entree, sortie, est_samedi, type_evenement):
        """Retourne les heures travaillées (HT) en décimal selon les règles existantes."""
        if not entree or not sortie:
            return 0.0
        ref = date.today()
        delta_minutes = (datetime.combine(ref, sortie) - datetime.combine(ref, entree)).total_seconds() / 60
        duree_heures = delta_minutes / 60.0
        if duree_heures <= 0:
            return 0.0

        if est_samedi:
            # Règle samedi : s'applique à X, HA, OS, PS
            if type_evenement in ('X', 'HA', 'OS', 'PS'):
                pause = 0.5 if duree_heures >= 6 else 0
                ht = duree_heures - pause
            else:
                ht = duree_heures
            return max(0, ht)

        # Jour normal (lundi à vendredi)
        if type_evenement == 'X':
            pause = 0.5 if duree_heures >= 8 else 0
            ht = duree_heures - pause
        elif type_evenement == 'HA':
            pause = 0.5 if duree_heures >= 8 else 0
            ht = duree_heures - pause
        elif type_evenement in ('OS', 'PS'):
            pause = 0.5 if duree_heures >= 8.5 else 0
            ht = duree_heures - pause
        else:
            ht = duree_heures
        return max(0, ht)

    def get(self, request):
        try:
            annee = int(request.query_params.get('annee', date.today().year))
            mois = int(request.query_params.get('mois', date.today().month))
            page = max(1, int(request.query_params.get('page', 1)))
            page_size = min(200, max(1, int(request.query_params.get('page_size', 50))))
        except ValueError:
            return Response({"error": "Paramètres invalides"}, status=400)

        section_filter = request.query_params.get('section', '').strip().upper()
        q = request.query_params.get('q', '').strip()

        from .utils import (
            build_user_section_map,
            analyser_pointages_jour,
            get_horaire_pour_date,
            get_active_userinfo_queryset,
        )

        # Dates de la période
        dates_mois_qs = Date.get_dates_par_mois(annee, mois, inclure_hors_periode=False)
        if not dates_mois_qs.exists():
            return Response({"error": "Générez d'abord les dates pour ce mois."}, status=400)

        dates_mois = list(dates_mois_qs)
        dates_liste = [d.date for d in dates_mois]

        # Regroupement par semaine
        semaines_dates = {}
        for d in dates_mois:
            s = d.code_date[0] if d.code_date else '1'
            semaines_dates.setdefault(s, []).append(d)
        semaine_nums = sorted(semaines_dates.keys())

        # Employés actifs
        user_section_map = build_user_section_map()
        users_qs = get_active_userinfo_queryset().order_by('badgenumber')

        if section_filter:
            ids_sec = {uid for uid, sec in user_section_map.items() if sec.upper() == section_filter}
            users_qs = users_qs.filter(userid__in=ids_sec)

        if q:
            users_qs = users_qs.filter(
                Q(name__icontains=q) | Q(badgenumber__icontains=q)
            )

        total_employees = users_qs.count()
        if total_employees == 0:
            return self._empty_response(annee, mois, dates_mois, semaine_nums, page, page_size)

        total_pages = (total_employees + page_size - 1) // page_size
        page = min(page, total_pages)
        users_page = list(users_qs[(page - 1) * page_size: page * page_size])
        user_ids = {u.userid for u in users_page}

        # Préchargements
        anomalies_map = {}
        for a in Anomalie.objects.filter(date__in=dates_liste, etat='ok', userid__in=user_ids):
            anomalies_map[(a.userid, a.date)] = a

        pointages_map = {}
        for p in CheckInOut.objects.filter(checktime__date__in=dates_liste, user_id__in=user_ids).values('user_id', 'checktime', 'checktype'):
            pointages_map.setdefault((p['user_id'], p['checktime'].date()), []).append(p)

        evenements_map = {}
        for ev in Evenement.objects.filter(userid__in=user_ids, date__in=dates_liste).values('userid', 'date', 'type_evenement'):
            evenements_map[(ev['userid'], ev['date'])] = ev['type_evenement']

        horaires_dict = {h.section: h for h in HoraireSection.objects.all()}
        horaire_default = horaires_dict.get('ADMINISTRATION')

        class FP:
            __slots__ = ('checktime', 'checktype')
            def __init__(self, d):
                self.checktime = d['checktime']
                self.checktype = d['checktype']

        # Calcul par employé
        results = []
        for user in users_page:
            section_emp = user_section_map.get(user.userid, 'ADMINISTRATION')
            horaire = horaires_dict.get(section_emp, horaire_default)

            par_semaine = {s: 0 for s in semaine_nums}
            jours_details = []
            total_jours = 0

            for date_obj in dates_mois:
                date_jour = date_obj.date
                semaine = date_obj.code_date[0] if date_obj.code_date else '1'
                key = (user.userid, date_jour)

                entree = sortie = None
                type_evenement = evenements_map.get(key, 'X')

                anomalie = anomalies_map.get(key)
                if anomalie and anomalie.heure_rectifiee_entree and anomalie.heure_rectifiee_sortie:
                    entree = anomalie.heure_rectifiee_entree
                    sortie = anomalie.heure_rectifiee_sortie
                elif key in pointages_map and horaire:
                    h_e, h_s = get_horaire_pour_date(
                        horaire, date_jour, date_obj.est_jour_paiement, section=section_emp
                    )
                    pts = [FP(p) for p in pointages_map[key]]
                    he, hs, type_a, _ = analyser_pointages_jour(pts, h_e, h_s, seuil_minutes=30)
                    if type_a is None and he and hs:
                        entree, sortie = he, hs

                ht = 0.0
                if entree and sortie:
                    est_samedi = (date_jour.weekday() == 5)
                    ht = self._heures_travaillees(entree, sortie, est_samedi, type_evenement)

                indemnite = ht >= 3.83
                if indemnite:
                    par_semaine[semaine] += 1
                    total_jours += 1

                jours_details.append({
                    'date': date_jour.isoformat(),
                    'code_date': date_obj.code_affichage,
                    'indemnite': indemnite,
                    'heures_travaillees': round(ht, 2)
                })

            results.append({
                'userid': user.userid,
                'badgenumber': user.badgenumber,
                'name': user.name,
                'section': section_emp,
                'par_semaine': par_semaine,
                'jours': jours_details,
                'total_jours': total_jours,
            })

        # Préparer les dates et numéros de semaine pour le front
        dates_serialized = [{'date': d.date.isoformat(), 'code_date': d.code_affichage} for d in dates_mois]

        mois_fr = ['Janvier','Février','Mars','Avril','Mai','Juin','Juillet','Août','Septembre','Octobre','Novembre','Décembre']
        mois_precedent = mois - 1 if mois > 1 else 12

        return Response({
            'periode': {
                'mois': mois_fr[mois - 1],
                'annee': annee,
                'du': f"21 {mois_fr[mois_precedent - 1]}",
                'au': f"20 {mois_fr[mois - 1]}",
            },
            'dates': dates_serialized,
            'semaines': semaine_nums,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_employees': total_employees,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_previous': page > 1,
            },
            'employes': results,
        })

    def _empty_response(self, annee, mois, dates_mois, semaine_nums, page, page_size):
        mois_fr = ['Janvier','Février','Mars','Avril','Mai','Juin','Juillet','Août','Septembre','Octobre','Novembre','Décembre']
        mois_precedent = mois - 1 if mois > 1 else 12
        dates_serialized = [{'date': d.date.isoformat(), 'code_date': d.code_affichage} for d in dates_mois]
        return Response({
            'periode': {
                'mois': mois_fr[mois - 1],
                'annee': annee,
                'du': f"21 {mois_fr[mois_precedent - 1]}",
                'au': f"20 {mois_fr[mois - 1]}",
            },
            'dates': dates_serialized,
            'semaines': semaine_nums,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_employees': 0,
                'total_pages': 0,
                'has_next': False,
                'has_previous': False,
            },
            'employes': [],
        })
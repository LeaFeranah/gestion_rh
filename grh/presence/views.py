from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.db.models import Min, Max, Q
from datetime import date, datetime
from .models import CheckInOut, UserInfo, Date, Evenement, HoraireSection, Anomalie
from .serializers import DateSerializer, HoraireSectionSerializer, EvenementSerializer, AnomalieSerializer
from .utils import decimal_to_time, analyser_presence, get_section_employe, corriger_pointages_automatique
import logging

logger = logging.getLogger(__name__)
# ========== GESTION DES DATES ==========

class DateGenerationAPIView(APIView):
    """
    Générer les dates pour un mois donné ET créer les événements par défaut
    GET /api/presence/generer-dates/?annee=2024&mois=8
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        annee = int(request.query_params.get('annee', date.today().year))
        mois = int(request.query_params.get('mois', date.today().month))
        
        # Générer les dates
        dates_crees = Date.generer_dates_mois(annee, mois)
        
        # CRÉER LES ÉVÉNEMENTS PAR DÉFAUT POUR TOUS LES EMPLOYÉS
        mois_ref = date(annee, mois, 1)
        dates_periode = Date.objects.filter(
            mois_reference=mois_ref,
            hors_periode=False
        ).values_list('date', flat=True)
        
        # Récupérer tous les employés
        employes = UserInfo.objects.all()
        
        evenements_crees = 0
        for employe in employes:
            for date_jour in dates_periode:
                # Créer l'événement "X" par défaut s'il n'existe pas
                _, created = Evenement.objects.get_or_create(
                    userid=employe.userid,
                    date=date_jour,
                    defaults={
                        'type_evenement': 'X',
                        'commentaire': 'Créé automatiquement'
                    }
                )
                if created:
                    evenements_crees += 1
        
        serializer = DateSerializer(dates_crees, many=True)
        
        mois_fr = [
            'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
        ]
        
        mois_precedent = mois - 1 if mois > 1 else 12
        
        return Response({
            "message": f"Dates générées pour {mois_fr[mois-1]} {annee}",
            "periode": f"21 {mois_fr[mois_precedent-1]} → 20 {mois_fr[mois-1]}",
            "count": len(dates_crees),
            "evenements_crees": evenements_crees,
            "dates": serializer.data
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
        
        employes = UserInfo.objects.all()
        
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
    """
    Présence détaillée d'un employé avec tous les calculs
    GET /api/presence/mois/detail/calculee/?annee=2024&mois=8
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
        
        # DÉFINIR LES VARIABLES DE MOIS ICI
        mois_fr = [
            'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
        ]
        mois_precedent = mois - 1 if mois > 1 else 12
        
        # Récupérer les dates du mois
        dates_mois = Date.get_dates_par_mois(annee, mois, inclure_hors_periode)
        dates_liste = list(dates_mois.values_list('date', flat=True))
        
        if not dates_liste:
            return Response({
                "message": f"Aucune date trouvée pour {mois}/{annee}. Générez d'abord les dates.",
                "dates_disponibles": []
            })
        
        # Créer un dictionnaire pour les dates avec leurs propriétés
        dates_dict = {}
        for date_obj in dates_mois:
            dates_dict[str(date_obj.date)] = {
                'date_obj': date_obj,
                'est_jour_paiement': date_obj.est_jour_paiement,
                'hors_periode': date_obj.hors_periode,
                'code_affichage': date_obj.code_affichage,
                'code_date': date_obj.code_date
            }
        
        # Récupérer tous les événements du mois (uniquement ceux qui ne sont pas 'X')
        evenements_query = Evenement.objects.filter(date__in=dates_liste)
        
        # Filtrer pour ne garder que les événements non-'X' ou les événements 'X' qui ont des présences
        # Nous allons filtrer plus tard dans la logique
        if badgenumber:
            user_ids = UserInfo.objects.filter(badgenumber=badgenumber).values_list('userid', flat=True)
            evenements_query = evenements_query.filter(userid__in=user_ids)
        
        # Créer un dictionnaire pour tous les événements
        evenements_dict = {}
        for e in evenements_query:
            evenements_dict[(e.userid, str(e.date))] = {
                'type': e.type_evenement,
                'commentaire': e.commentaire
            }
        
        # RÉCUPÉRER LES ANOMALIES CORRIGÉES (état='ok')
        anomalies_corrigees = Anomalie.objects.filter(
            date__in=dates_liste,
            etat='ok'
        ).select_related()
        
        # Créer un dictionnaire pour accéder rapidement aux anomalies corrigées
        anomalies_corrigees_dict = {}
        for anomalie in anomalies_corrigees:
            key = (anomalie.userid, str(anomalie.date))
            anomalies_corrigees_dict[key] = {
                'heure_entree': anomalie.heure_reelle_entree,
                'heure_sortie': anomalie.heure_reelle_sortie,
                'heure_rectifiee_entree': anomalie.heure_rectifiee_entree,
                'heure_rectifiee_sortie': anomalie.heure_rectifiee_sortie,
                'heure_brute_entree': anomalie.heure_brute_entree,
                'heure_brute_sortie': anomalie.heure_brute_sortie,
                'est_anomalie_corrigee': True,
                'section': anomalie.section,
                'synchronise_le': anomalie.synchronise_le,
            }
        
        # Récupérer les pointages pour construire une liste des users avec présence
        pointages_query = CheckInOut.objects.filter(checktime__date__in=dates_liste)
        if badgenumber:
            pointages_query = pointages_query.filter(user__badgenumber=badgenumber)
        
        # Créer un ensemble des userids qui ont des pointages
        userids_avec_pointages = set(pointages_query.values_list('user__userid', flat=True).distinct())
        
        # Créer un ensemble des userids qui ont des anomalies corrigées
        userids_avec_anomalies = set([key[0] for key in anomalies_corrigees_dict.keys()])
        
        # Combiner - ce sont les users qui ont soit des pointages, soit des anomalies
        userids_a_traiter = userids_avec_pointages.union(userids_avec_anomalies)
        
        # Si pas d'utilisateurs à traiter
        if not userids_a_traiter:
            return Response({
                "periode": {
                    "mois": mois_fr[mois - 1],
                    "annee": annee,
                    "du": f"21 {mois_fr[mois_precedent - 1]}",
                    "au": f"20 {mois_fr[mois - 1]}",
                    "nombre_jours": len(dates_liste)
                },
                "presences": [],
                "statistiques": {
                    "total_presences": 0
                }
            })
        
        # Récupérer les informations des utilisateurs
        users = UserInfo.objects.filter(userid__in=userids_a_traiter)
        if badgenumber:
            users = users.filter(badgenumber=badgenumber)
        
        resultat = []
        
        for user in users:
            # Pour chaque date du mois
            for date_str in dates_liste:
                date_str = str(date_str)
                date_info = dates_dict.get(date_str)
                
                if not date_info:
                    continue
                
                date_obj = date_info['date_obj']
                est_jour_paiement = date_info['est_jour_paiement']
                
                # VÉRIFIER SI ON A UNE ANOMALIE CORRIGÉE
                pointage_key = (user.userid, date_str)
                anomalie_corrigee = anomalies_corrigees_dict.get(pointage_key)
                est_anomalie_corrigee = anomalie_corrigee is not None
                
                # Récupérer la section
                if est_anomalie_corrigee:
                    section = anomalie_corrigee.get('section') or get_section_employe(user.badgenumber)
                else:
                    section = get_section_employe(user.badgenumber)
                
                # Récupérer l'horaire de la section
                try:
                    horaire = HoraireSection.objects.get(section=section)
                except HoraireSection.DoesNotExist:
                    try:
                        horaire = HoraireSection.objects.get(section='ADMINISTRATION')
                    except HoraireSection.DoesNotExist:
                        continue
                
                date_pointage = datetime.strptime(date_str, "%Y-%m-%d").date()
                est_samedi = date_pointage.weekday() == 5
                est_vendredi = date_pointage.weekday() == 4
                
                # DÉTERMINER L'HEURE DE SORTIE PRÉVUE
                if est_jour_paiement:
                    if est_vendredi:
                        heure_sortie_prevue_decimal = horaire.sortie_vendredi_paiement
                    else:
                        heure_sortie_prevue_decimal = horaire.sortie_samedi_paiement
                elif est_samedi:
                    heure_sortie_prevue_decimal = horaire.sortie_samedi
                else:
                    heure_sortie_prevue_decimal = horaire.heure_sortie
                
                heure_entree_prevue = decimal_to_time(horaire.heure_entree)
                heure_sortie_prevue = decimal_to_time(heure_sortie_prevue_decimal)
                
                # DÉTERMINER LES HEURES RÉELLES ET BRUTES
                if est_anomalie_corrigee:
                    # Utiliser les heures de l'anomalie corrigée
                    heure_entree_reelle = anomalie_corrigee['heure_entree']
                    heure_sortie_reelle = anomalie_corrigee['heure_sortie']
                    heure_entree_rectifiee = anomalie_corrigee['heure_rectifiee_entree']
                    heure_sortie_rectifiee = anomalie_corrigee['heure_rectifiee_sortie']
                    # Heures brutes sont celles de l'anomalie
                    heure_brute_entree = anomalie_corrigee['heure_brute_entree']
                    heure_brute_sortie = anomalie_corrigee['heure_brute_sortie']
                    synchronise_le = anomalie_corrigee['synchronise_le']
                    present = heure_entree_reelle is not None or heure_sortie_reelle is not None
                else:
                    # Récupérer les pointages bruts pour cette date
                    pointages_bruts = CheckInOut.objects.filter(
                        user=user,
                        checktime__date=date_str
                    )
                    

                    if pointages_bruts.exists():
                        from .utils import analyser_pointages_jour
                        pointages_list = list(pointages_bruts)
                        tries = sorted(pointages_list, key=lambda p: p.checktime)

                        entrees_brutes = [p for p in tries if p.checktype.upper() == 'O']
                        sorties_brutes  = [p for p in tries if p.checktype.upper() == 'I']
                        has_mixed = bool(entrees_brutes and sorties_brutes)

                        if len(tries) == 1:
                            p = tries[0]
                            if p.checktype.upper() == 'I':
                                # Seul I → entrée vide
                                heure_brute_entree = None
                                heure_brute_sortie = p.checktime.time()
                            else:
                                # Seul O → sortie vide
                                heure_brute_entree = p.checktime.time()
                                heure_brute_sortie = None

                        elif has_mixed:
                            # O+I ou I+O → brutes basées sur le checktype (même si inversé)
                            heure_brute_entree = entrees_brutes[0].checktime.time()
                            heure_brute_sortie = sorties_brutes[-1].checktime.time()

                        else:
                            # I+I ou O+O → premier=entrée brute, dernier=sortie brute (chronologique)
                            heure_brute_entree = tries[0].checktime.time()
                            heure_brute_sortie = tries[-1].checktime.time()

                        # ── Heures rectifiées via analyser_pointages_jour ──────────────────────
                        heure_entree_calc, heure_sortie_calc, type_anomalie_calc, _ = analyser_pointages_jour(
                            pointages_list, heure_entree_prevue, heure_sortie_prevue, seuil_minutes=30
                        )

                        heure_entree_reelle = heure_entree_calc
                        heure_sortie_reelle = heure_sortie_calc
                        present = True
                       
                    else:
                        heure_entree_reelle = None
                        heure_sortie_reelle = None
                        heure_brute_entree = None
                        heure_brute_sortie = None
                        present = False
                    
                    heure_entree_rectifiee = heure_entree_reelle
                    heure_sortie_rectifiee = heure_sortie_reelle
                    synchronise_le = None
                
                # NOUVELLE LOGIQUE: Si pas présent, pas d'anomalie corrigée, ET pas d'événement spécial -> sauter
                evenement_data = evenements_dict.get(pointage_key)
                has_special_event = evenement_data and evenement_data['type'] != 'X'
                
                # Ne pas inclure si:
                # 1. Pas de présence (pointage)
                # 2. Pas d'anomalie corrigée
                # 3. Pas d'événement spécial (ou événement = 'X')
                if not present and not est_anomalie_corrigee and not has_special_event:
                    continue
                
                # Déterminer l'événement à afficher
                if evenement_data:
                    evenement = evenement_data['type']
                else:
                    # Si pas d'événement enregistré, utiliser 'X' par défaut
                    evenement = 'X'
                
                # ANALYSE DE LA PRÉSENCE
                heure_entree_pour_analyse = heure_entree_rectifiee if est_anomalie_corrigee else heure_entree_reelle
                heure_sortie_pour_analyse = heure_sortie_rectifiee if est_anomalie_corrigee else heure_sortie_reelle
                
                # Si les deux heures sont None, on peut considérer comme absent
                if not heure_entree_pour_analyse and not heure_sortie_pour_analyse:
                    # Si c'est une anomalie corrigée avec heures nulles, c'est une absence confirmée
                    if est_anomalie_corrigee:
                        analyse = {
                            'heure_entree_comptabilisee': None,
                            'heure_sortie_comptabilisee': None,
                            'retard_minutes': 0,
                            'sortie_anticipee_minutes': 0,
                            'heures_travaillees': 0.0,
                            'heures_prevues': 0.0,
                            'est_en_retard': False,
                            'est_sorti_en_avance': False,
                            'difference_heures': 0.0,
                        }
                    else:
                        # Pas de pointage et pas d'anomalie corrigée, passer
                        continue
                else:
                    # Au moins une heure existe, analyser
                    analyse = analyser_presence(
                        heure_entree_pour_analyse,
                        heure_sortie_pour_analyse,
                        heure_entree_prevue,
                        heure_sortie_prevue,
                        date_pointage
                    )
                
                # Ajouter au résultat
                resultat.append({
                    "userid": user.userid,
                    "badgenumber": user.badgenumber,
                    "name": user.name,
                    "section": section,
                    "date": date_str,
                    "code_date": date_obj.code_date,
                    "code_affichage": date_obj.code_affichage,
                    "hors_periode": date_obj.hors_periode,
                    "est_samedi": est_samedi,
                    "est_vendredi": est_vendredi,
                    "est_jour_paiement": est_jour_paiement,
                    "est_anomalie_corrigee": est_anomalie_corrigee,
                    "synchronise_le": str(synchronise_le) if synchronise_le else None,
                    "present": present,
                    
                    # Heures brutes (originales) - TOUJOURS renvoyées
                    "heure_brute_entree": str(heure_brute_entree) if heure_brute_entree else None,
                    "heure_brute_sortie": str(heure_brute_sortie) if heure_brute_sortie else None,
                    
                    # Heures réelles (de la section)
                    "heure_entree_reelle": str(heure_entree_reelle) if heure_entree_reelle else None,
                    "heure_sortie_reelle": str(heure_sortie_reelle) if heure_sortie_reelle else None,
                    
                    # Heures rectifiées (après correction)
                    "heure_entree_rectifiee": str(heure_entree_rectifiee) if heure_entree_rectifiee else None,
                    "heure_sortie_rectifiee": str(heure_sortie_rectifiee) if heure_sortie_rectifiee else None,
                    
                    # Heures prévues
                    "heure_entree_prevue": str(heure_entree_prevue),
                    "heure_sortie_prevue": str(heure_sortie_prevue),
                    "type_sortie_prevue": "vendredi_paiement" if est_jour_paiement and est_vendredi else 
                                         "samedi_paiement" if est_jour_paiement and est_samedi else
                                         "samedi_normal" if est_samedi else "normal",
                    
                    # Heures comptabilisées (après analyse)
                    "heure_entree_comptabilisee": str(analyse['heure_entree_comptabilisee']) if analyse['heure_entree_comptabilisee'] else None,
                    "heure_sortie_comptabilisee": str(analyse['heure_sortie_comptabilisee']) if analyse['heure_sortie_comptabilisee'] else None,
                    
                    # Analyses
                    "retard_minutes": analyse['retard_minutes'],
                    "sortie_anticipee_minutes": analyse['sortie_anticipee_minutes'],
                    "heures_travaillees": analyse['heures_travaillees'],
                    "heures_prevues": analyse['heures_prevues'],
                    "est_en_retard": analyse['est_en_retard'],
                    "est_sorti_en_avance": analyse['est_sorti_en_avance'],
                    "difference_heures": analyse['difference_heures'],
                    
                    "evenement": evenement,
                    "has_special_event": has_special_event  # Ajouter cette information pour le front
                })
        
        # Trier les résultats par badge number et date
        resultat.sort(key=lambda x: (x['badgenumber'], x['date']))
        
        # Calculer les statistiques
        total_retard_minutes = sum(r.get('retard_minutes', 0) for r in resultat)
        total_sortie_anticipee_minutes = sum(r.get('sortie_anticipee_minutes', 0) for r in resultat)
        total_heures_travaillees = sum(r.get('heures_travaillees', 0) for r in resultat)
        total_heures_prevues = sum(r.get('heures_prevues', 0) for r in resultat)
        total_anomalies_corrigees = sum(1 for r in resultat if r.get('est_anomalie_corrigee', False))
        total_with_special_events = sum(1 for r in resultat if r.get('has_special_event', False))
        
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
                "nombre_retards": sum(1 for r in resultat if r.get('est_en_retard', False)),
                "nombre_sorties_anticipees": sum(1 for r in resultat if r.get('est_sorti_en_avance', False)),
                "nombre_jours_paiement": sum(1 for r in resultat if r.get('est_jour_paiement', False)),
                "nombre_anomalies_corrigees": total_anomalies_corrigees,
                "nombre_evenements_speciaux": total_with_special_events,
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
            if anomalie_updated.etat == 'ok':
                # Optionnel : synchroniser avec CheckInOut si nécessaire
                self._synchroniser_avec_checkinout(anomalie_updated)
            
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


class DetecterAnomaliesAPIView(APIView):
    """
    Détecte automatiquement les anomalies pour une période
    POST /api/presence/detecter-anomalies/
    Body: {"annee": 2024, "mois": 8}
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        annee = request.data.get('annee')
        mois = request.data.get('mois')
        
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
        
        # Récupérer les dates de la période
        dates_mois = Date.get_dates_par_mois(annee, mois, inclure_hors_periode=False)
        
        total_anomalies = 0
        for date_obj in dates_mois:
            count = Anomalie.detecter_anomalies_jour(date_obj.date)
            total_anomalies += count
        
        # Statistiques détaillées
        anomalies = Anomalie.objects.filter(date__in=dates_mois.values_list('date', flat=True))
        stats_par_etat = {}
        for etat_code, etat_libelle in Anomalie.ETATS_ANOMALIE:
            count = anomalies.filter(etat=etat_code).count()
            if count > 0:
                stats_par_etat[etat_code] = {
                    'libelle': etat_libelle,
                    'count': count
                }
        
        return Response({
            'message': f'{total_anomalies} anomalies détectées pour {mois}/{annee}',
            'total': total_anomalies,
            'periode': {
                'annee': annee,
                'mois': mois,
                'jours_analyses': dates_mois.count()
            },
            'statistiques': {
                'par_etat': stats_par_etat,
                'total_corrigees': anomalies.filter(etat='ok').count(),
                'total_non_corrigees': anomalies.exclude(etat='ok').count()
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

            # --- RÉCUPÉRATION DES HEURES BRUTES (pointages d'origine) ---
            # On interroge la table CheckInOut pour obtenir les vrais pointages du jour
            pointages_bruts = CheckInOut.objects.filter(
                user=user,
                checktime__date=date_jour
            ).order_by('checktime')

            heure_brute_entree = None
            heure_brute_sortie = None
            if pointages_bruts.exists():
                # Premier pointage = entrée brute
                heure_brute_entree = pointages_bruts[0].checktime.time()
                # Dernier pointage = sortie brute (si plusieurs)
                if len(pointages_bruts) > 1:
                    heure_brute_sortie = pointages_bruts[-1].checktime.time()
                # Si un seul pointage, la sortie brute reste None (absence de sortie)

            # --- CRÉATION / MISE À JOUR DE L'ANOMALIE ---
            # On conserve systématiquement les heures brutes, on ne les écrase jamais.
            # Les heures rectifiées sont celles saisies par l'utilisateur.
            anomalie, created = Anomalie.objects.update_or_create(
                userid=userid,
                date=date_jour,
                defaults={
                    'section': section,
                    'code_date': code_date,
                    'heure_brute_entree': heure_brute_entree,   # ← inchangées, jamais None sauf si aucun pointage
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

            # ⚠️ SUPPRESSION DE TOUTE SYNCHRONISATION AVEC CheckInOut
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
        
        # Rechercher par badge ou nom
        employees = UserInfo.objects.filter(
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
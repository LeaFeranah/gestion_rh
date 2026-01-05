# # # from rest_framework.views import APIView
# # # from rest_framework.response import Response
# # # from rest_framework.permissions import AllowAny
# # # from django.db.models import Min, Max
# # # from .models import CheckInOut


# # # class PresenceAPIView(APIView):
# # #     """
# # #     API de gestion de présence
# # #     - Groupement par date
# # #     - Première heure = entrée
# # #     - Dernière heure = sortie
# # #     """
# # #     permission_classes = [AllowAny]

# # #     def get(self, request, user_id):
# # #         """
# # #         user_id = valeur de la colonne checkinout.userid
# # #         """

# # #         # 🔹 Regrouper les pointages par date
# # #         pointages = (
# # #             CheckInOut.objects
# # #             .filter(user_id=user_id)  # IMPORTANT
# # #             .values('checktime__date')
# # #             .annotate(
# # #                 heure_entree=Min('checktime'),
# # #                 heure_sortie=Max('checktime')
# # #             )
# # #             .order_by('checktime__date')
# # #         )

# # #         resultat = []

# # #         for p in pointages:
# # #             resultat.append({
# # #                 "date": p["checktime__date"],
# # #                 "heure_entree": p["heure_entree"].time() if p["heure_entree"] else None,
# # #                 "heure_sortie": p["heure_sortie"].time() if p["heure_sortie"] else None,
# # #                 "evenement": "X"  # Travail normal par défaut
# # #             })

# # #         return Response(resultat)


# # from rest_framework.views import APIView
# # from rest_framework.response import Response
# # from rest_framework.permissions import AllowAny
# # from django.db.models import Min, Max
# # from .models import CheckInOut, UserInfo


# # class PresenceAPIView(APIView):
# #     """
# #     API de gestion de présence
# #     - Groupement par date
# #     - Première heure = entrée
# #     - Dernière heure = sortie
# #     - Affiche badgenumber et name de l'utilisateur
# #     """
# #     permission_classes = [AllowAny]

# #     def get(self, request, user_id):
# #         """
# #         user_id = valeur de la colonne checkinout.userid
# #         """
        
# #         # 🔹 Récupérer les infos de l'utilisateur
# #         try:
# #             user_info = UserInfo.objects.get(userid=user_id)
# #         except UserInfo.DoesNotExist:
# #             return Response(
# #                 {"error": f"Utilisateur avec userid={user_id} non trouvé"}, 
# #                 status=404
# #             )

# #         # 🔹 Regrouper les pointages par date
# #         pointages = (
# #             CheckInOut.objects
# #             .filter(user_id=user_id)
# #             .values('checktime__date')
# #             .annotate(
# #                 heure_entree=Min('checktime'),
# #                 heure_sortie=Max('checktime')
# #             )
# #             .order_by('checktime__date')
# #         )

# #         resultat = []

# #         for p in pointages:
# #             resultat.append({
# #                 "badgenumber": user_info.badgenumber,
# #                 "name": user_info.name,
# #                 "date": p["checktime__date"],
# #                 "heure_entree": p["heure_entree"].time() if p["heure_entree"] else None,
# #                 "heure_sortie": p["heure_sortie"].time() if p["heure_sortie"] else None,
# #                 "evenement": "X"  # Travail normal par défaut
# #             })

# #         return Response(resultat)


# # from rest_framework.views import APIView
# # from rest_framework.response import Response
# # from rest_framework.permissions import AllowAny
# # from django.db.models import Min, Max
# # from .models import CheckInOut, UserInfo


# # class PresenceAPIView(APIView):
# #     """
# #     API de gestion de présence
# #     - Groupement par date
# #     - Première heure = entrée
# #     - Dernière heure = sortie
# #     - Affiche badgenumber et name de l'utilisateur
# #     """
# #     permission_classes = [AllowAny]

# #     def get(self, request, badgenumber):
# #         """
# #         badgenumber = numéro de badge de l'utilisateur
# #         """
        
# #         # 🔹 Récupérer les infos de l'utilisateur via badgenumber
# #         try:
# #             user_info = UserInfo.objects.get(badgenumber=badgenumber)
# #         except UserInfo.DoesNotExist:
# #             return Response(
# #                 {"error": f"Utilisateur avec badgenumber={badgenumber} non trouvé"}, 
# #                 status=404
# #             )

# #         # 🔹 Regrouper les pointages par date
# #         pointages = (
# #             CheckInOut.objects
# #             .filter(user__badgenumber=badgenumber)  # 🔹 Filtrer par badgenumber
# #             .values('checktime__date')
# #             .annotate(
# #                 heure_entree=Min('checktime'),
# #                 heure_sortie=Max('checktime')
# #             )
# #             .order_by('checktime__date')
# #         )

# #         resultat = []

# #         for p in pointages:
# #             resultat.append({
# #                 "userid": user_info.userid,
# #                 "badgenumber": user_info.badgenumber,
# #                 "name": user_info.name,
# #                 "date": p["checktime__date"],
# #                 "heure_entree": p["heure_entree"].time() if p["heure_entree"] else None,
# #                 "heure_sortie": p["heure_sortie"].time() if p["heure_sortie"] else None,
# #                 "evenement": "X"  # Travail normal par défaut
# #             })

# #         return Response(resultat)


# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import AllowAny
# from django.db.models import Min, Max
# from .models import CheckInOut, UserInfo


# class PresenceListAPIView(APIView):
#     """
#     API pour afficher toutes les présences de tous les utilisateurs
#     """
#     permission_classes = [AllowAny]

#     def get(self, request):
#         """
#         Retourne toutes les présences groupées par utilisateur et par date
#         """
        
#         # 🔹 Regrouper les pointages par utilisateur et par date
#         pointages = (
#             CheckInOut.objects
#             .select_related('user')  # Optimisation pour éviter les requêtes multiples
#             .values('user__userid', 'user__badgenumber', 'user__name', 'checktime__date')
#             .annotate(
#                 heure_entree=Min('checktime'),
#                 heure_sortie=Max('checktime')
#             )
#             .order_by('user__badgenumber', 'checktime__date')
#         )

#         resultat = []

#         for p in pointages:
#             resultat.append({
#                 "userid": p["user__userid"],
#                 "badgenumber": p["user__badgenumber"],
#                 "name": p["user__name"],
#                 "date": p["checktime__date"],
#                 "heure_entree": p["heure_entree"].time() if p["heure_entree"] else None,
#                 "heure_sortie": p["heure_sortie"].time() if p["heure_sortie"] else None,
#                 "evenement": "X"  # Travail normal par défaut
#             })

#         return Response(resultat)


# class PresenceAPIView(APIView):
#     """
#     API de gestion de présence par badgenumber
#     - Groupement par date
#     - Première heure = entrée
#     - Dernière heure = sortie
#     - Affiche badgenumber et name de l'utilisateur
#     """
#     permission_classes = [AllowAny]

#     def get(self, request, badgenumber):
#         """
#         badgenumber = numéro de badge de l'utilisateur
#         """
        
#         # 🔹 Récupérer les infos de l'utilisateur via badgenumber
#         try:
#             user_info = UserInfo.objects.get(badgenumber=badgenumber)
#         except UserInfo.DoesNotExist:
#             return Response(
#                 {"error": f"Utilisateur avec badgenumber={badgenumber} non trouvé"}, 
#                 status=404
#             )

#         # 🔹 Regrouper les pointages par date
#         pointages = (
#             CheckInOut.objects
#             .filter(user__badgenumber=badgenumber)
#             .values('checktime__date')
#             .annotate(
#                 heure_entree=Min('checktime'),
#                 heure_sortie=Max('checktime')
#             )
#             .order_by('checktime__date')
#         )

#         resultat = []

#         for p in pointages:
#             resultat.append({
#                 "userid": user_info.userid,
#                 "badgenumber": user_info.badgenumber,
#                 "name": user_info.name,
#                 "date": p["checktime__date"],
#                 "heure_entree": p["heure_entree"].time() if p["heure_entree"] else None,
#                 "heure_sortie": p["heure_sortie"].time() if p["heure_sortie"] else None,
#                 "evenement": "X"  # Travail normal par défaut
#             })

#         return Response(resultat)


# presence/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Min, Max
from datetime import date
from .models import CheckInOut, UserInfo, Date
from .serializers import DateSerializer


# ========== NOUVELLES VUES (AVEC TABLE DATE) ==========

class DateGenerationAPIView(APIView):
    """
    Générer les dates pour un mois donné
    GET /api/presence/generer-dates/?annee=2024&mois=8
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        annee = int(request.query_params.get('annee', date.today().year))
        mois = int(request.query_params.get('mois', date.today().month))
        
        dates_crees = Date.generer_dates_mois(annee, mois)
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


class PresenceMoisAPIView(APIView):
    """
    Vue principale : Présences d'un mois avec codes dates
    GET /api/presence/mois/?annee=2024&mois=8
    GET /api/presence/mois/?annee=2024&mois=8&badgenumber=123
    GET /api/presence/mois/?annee=2024&mois=8&inclure_hors_periode=true
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


# ========== ANCIENNES VUES (SANS TABLE DATE) ==========

class PresenceListAPIView(APIView):
    """
    API pour afficher toutes les présences de tous les utilisateurs (ANCIENNE VERSION)
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
    API de gestion de présence par badgenumber (ANCIENNE VERSION)
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
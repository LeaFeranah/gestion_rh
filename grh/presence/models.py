# # from django.db import models

# # # ===== USERINFO =====
# # class UserInfo(models.Model):
# #     userid01 = models.IntegerField(db_column='userid01', primary_key=True)
# #     userid = models.IntegerField(db_column='userid')
# #     badgenumber = models.CharField(db_column='badgenumber', max_length=50)
# #     ssn = models.CharField(db_column='ssn', max_length=50, null=True, blank=True)
# #     name = models.CharField(db_column='name', max_length=150)

# #     class Meta:
# #         db_table = 'userinfo'  # nom table en minuscules
# #         managed = False

# #     def __str__(self):
# #         return self.name


# # # ===== CHECKINOUT =====
# # class CheckInOut(models.Model):
# #     numauto = models.AutoField(db_column='numauto', primary_key=True)
# #     user = models.ForeignKey(
# #         UserInfo,
# #         db_column='userid',  # colonne dans checkinout
# #         on_delete=models.DO_NOTHING
# #     )
# #     checktime = models.DateTimeField(db_column='checktime')
# #     checktype = models.CharField(db_column='checktype', max_length=1)

# #     class Meta:
# #         db_table = 'checkinout'  # nom table en minuscules
# #         managed = False



# from django.db import models

# # ===== USERINFO =====
# class UserInfo(models.Model):
#     userid = models.IntegerField(db_column='userid', primary_key=True)
#     badgenumber = models.CharField(db_column='Badgenumber', max_length=50)  # 🔹 Majuscule
#     ssn = models.CharField(db_column='ssn', max_length=50, null=True, blank=True)
#     name = models.CharField(db_column='Name', max_length=150)  # 🔹 Majuscule

#     class Meta:
#         db_table = 'userinfo'
#         managed = False

#     def __str__(self):
#         return self.name


# # ===== CHECKINOUT =====
# class CheckInOut(models.Model):
#     numauto = models.AutoField(db_column='NumAuto', primary_key=True)  # 🔹 Majuscules
#     user = models.ForeignKey(
#         UserInfo,
#         db_column='userid',
#         on_delete=models.DO_NOTHING
#     )
#     checktime = models.DateTimeField(db_column='checktime')
#     checktype = models.CharField(db_column='checktype', max_length=1)

#     class Meta:
#         db_table = 'checkinout'
#         managed = False





# presence/models.py

from django.db import models
from datetime import date, timedelta


# ===== TABLE DATE =====
class Date(models.Model):
    date = models.DateField(unique=True, primary_key=True)
    code_date = models.CharField(max_length=2)  # 11, 12, 13... 57
    hors_periode = models.BooleanField(default=False)  # True = F (hors période)
    mois_reference = models.DateField()  # Ex: 2024-08-01 pour le mois d'août
    
    class Meta:
        db_table = 'date'
        ordering = ['date']
    
    def __str__(self):
        if self.hors_periode:
            return f"{self.date} - {self.code_date}F (Hors période)"
        return f"{self.date} - {self.code_date}"
    
    @property
    def code_affichage(self):
        """Code à afficher : '11F' ou '11'"""
        return f"{self.code_date}F" if self.hors_periode else self.code_date
    
    @staticmethod
    def get_lundi_precedent(d):
        """Retourne le lundi précédent ou égal à la date donnée"""
        jours_depuis_lundi = d.weekday()  # 0 = lundi, 6 = dimanche
        return d - timedelta(days=jours_depuis_lundi)
    
    @staticmethod
    def calculer_code_date(d, lundi_debut):
        """
        Calcule le code_date pour une date donnée (toujours calculé)
        d: date à analyser
        lundi_debut: premier lundi de la période
        """
        jours_depuis_debut = (d - lundi_debut).days
        numero_semaine = (jours_depuis_debut // 7) + 1
        jour_semaine = (d.weekday() + 1)  # 1 = lundi, 7 = dimanche
        
        # Limiter à 5 semaines max
        if numero_semaine > 5:
            numero_semaine = 5
        
        return f"{numero_semaine}{jour_semaine}"
    
    @classmethod
    def generer_dates_mois(cls, annee, mois):
        """
        Génère toutes les dates pour un mois de référence donné
        Ex: mois=8 (août) → période du 21 juillet au 20 août
        """
        mois_ref = date(annee, mois, 1)
        
        # ✅ Période du 21 du mois précédent au 20 du mois courant
        if mois == 1:
            debut_periode = date(annee - 1, 12, 21)
        else:
            debut_periode = date(annee, mois - 1, 21)
        
        fin_periode = date(annee, mois, 20)
        
        # ✅ Commencer au lundi précédent ou égal au 21
        lundi_debut = cls.get_lundi_precedent(debut_periode)
        
        # ✅ Générer toutes les dates (6 semaines complètes)
        date_courante = lundi_debut
        dates_crees = []
        
        fin_generation = lundi_debut + timedelta(days=6*7-1)  # 6 semaines
        
        while date_courante <= fin_generation:
            # ✅ Toujours calculer le code_date
            code = cls.calculer_code_date(date_courante, lundi_debut)
            
            # ✅ Déterminer si hors période (F)
            hors_periode = (date_courante < debut_periode or date_courante > fin_periode)
            
            obj, created = cls.objects.update_or_create(
                date=date_courante,
                defaults={
                    'code_date': code,
                    'hors_periode': hors_periode,
                    'mois_reference': mois_ref
                }
            )
            dates_crees.append(obj)
            date_courante += timedelta(days=1)
        
        return dates_crees
    
    @classmethod
    def get_dates_par_mois(cls, annee, mois, inclure_hors_periode=False):
        """
        Retourne toutes les dates pour un mois de référence
        """
        mois_ref = date(annee, mois, 1)
        
        if inclure_hors_periode:
            return cls.objects.filter(mois_reference=mois_ref).order_by('date')
        else:
            return cls.objects.filter(
                mois_reference=mois_ref,
                hors_periode=False
            ).order_by('date')


# ===== USERINFO =====
class UserInfo(models.Model):
    userid = models.IntegerField(db_column='userid', primary_key=True)
    badgenumber = models.CharField(db_column='Badgenumber', max_length=50)
    ssn = models.CharField(db_column='ssn', max_length=50, null=True, blank=True)
    name = models.CharField(db_column='Name', max_length=150)

    class Meta:
        db_table = 'userinfo'
        managed = False

    def __str__(self):
        return self.name


# ===== CHECKINOUT =====
class CheckInOut(models.Model):
    numauto = models.AutoField(db_column='NumAuto', primary_key=True)
    user = models.ForeignKey(
        UserInfo,
        db_column='userid',
        on_delete=models.DO_NOTHING
    )
    checktime = models.DateTimeField(db_column='checktime')
    checktype = models.CharField(db_column='checktype', max_length=1)

    class Meta:
        db_table = 'checkinout'
        managed = False
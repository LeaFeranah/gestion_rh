from django.db import models
from datetime import date, timedelta

class Date(models.Model):
    date = models.DateField(unique=True, primary_key=True)
    code_date = models.CharField(max_length=2)  
    hors_periode = models.BooleanField(default=False)  
    mois_reference = models.DateField()  
    
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
        
        # Période du 21 du mois précédent au 20 du mois courant
        if mois == 1:
            debut_periode = date(annee - 1, 12, 21)
        else:
            debut_periode = date(annee, mois - 1, 21)
        
        fin_periode = date(annee, mois, 20)
        
        # Commencer au lundi précédent ou égal au 21
        lundi_debut = cls.get_lundi_precedent(debut_periode)
        
        # Générer toutes les dates (6 semaines complètes)
        date_courante = lundi_debut
        dates_crees = []
        
        fin_generation = lundi_debut + timedelta(days=6*7-1)  # 6 semaines
        
        while date_courante <= fin_generation:
            # Toujours calculer le code_date
            code = cls.calculer_code_date(date_courante, lundi_debut)
            
            # Déterminer si hors période (F)
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


# ===== HORAIRES PAR SECTION =====
class HoraireSection(models.Model):
    """
    Horaires de référence par section
    Les heures sont stockées en format décimal (ex: 7.50 = 7h30, 17.83 = 17h50)
    """
    section = models.CharField(max_length=100, unique=True, primary_key=True)
    heure_entree = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        help_text="Heure d'entrée en format décimal (ex: 7.50 = 7h30)"
    )
    heure_sortie = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        help_text="Heure de sortie en format décimal (ex: 17.83 = 17h50)"
    )
    sortie_samedi = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        help_text="Heure de sortie le samedi en format décimal"
    )
    
    class Meta:
        db_table = 'horaire_section'
        verbose_name = "Horaire de section"
        verbose_name_plural = "Horaires de section"
        ordering = ['section']
    
    def __str__(self):
        return f"{self.section} ({self.heure_entree_normale} - {self.heure_sortie_normale})"
    
    @staticmethod
    def decimal_to_time(heure_decimal):
        """
        Convertit une heure décimale en format HH:MM
        Ex: 7.50 -> "07:30", 17.83 -> "17:50"
        """
        heures = int(heure_decimal)
        minutes_decimal = (heure_decimal - heures) * 100
        minutes = int(round(minutes_decimal))
        return f"{heures:02d}:{minutes:02d}"
    
    @staticmethod
    def time_to_decimal(heure_str):
        """
        Convertit un format HH:MM en décimal
        Ex: "07:30" -> 7.50, "17:50" -> 17.83
        """
        from datetime import datetime
        time_obj = datetime.strptime(heure_str, "%H:%M").time()
        heures = time_obj.hour
        minutes = time_obj.minute
        return heures + (minutes / 60 * 100) / 100
    
    @property
    def heure_entree_normale(self):
        """Retourne l'heure d'entrée au format HH:MM"""
        return self.decimal_to_time(self.heure_entree)
    
    @property
    def heure_sortie_normale(self):
        """Retourne l'heure de sortie au format HH:MM"""
        return self.decimal_to_time(self.heure_sortie)
    
    @property
    def sortie_samedi_normale(self):
        """Retourne l'heure de sortie samedi au format HH:MM"""
        return self.decimal_to_time(self.sortie_samedi)
    
    @classmethod
    def initialiser_horaires(cls):
        """
        Initialise les horaires de toutes les sections
        À appeler une seule fois pour créer les données initiales
        """
        horaires_data = [
            ('ADMINISTRATION', 7.50, 17.83, 15.50),
            ('BRODERIE MACHINE', 7.50, 18.00, 15.50),
            ('BRODERIE MAIN AK B', 7.33, 17.33, 15.33),
            ('BRODERIE MAIN AK17', 7.00, 17.00, 15.00),
            ('BRODERIE MAIN DEV', 7.50, 18.00, 15.50),
            ('BUREAU DE METHODE', 7.41, 17.91, 12.00),
            ('CONTROLE QUALITE AS', 7.50, 17.50, 15.50),
            ('CHAINE 1', 7.41, 17.91, 15.41),
            ('CHAINE 2', 7.41, 17.91, 15.41),
            ('CHAINE 3', 7.41, 17.91, 15.41),
            ('CHAINE 4', 7.41, 17.91, 15.41),
            ('CHAINE 5', 7.41, 17.91, 15.41),
            ('CHAINE 6', 7.41, 17.91, 15.41),
            ('CHAINE 7', 7.41, 17.91, 15.41),
            ('CHAINE 8', 7.41, 17.91, 15.41),
            ('PACKING/EXPEDITION', 7.50, 18.00, 15.50),
            ('PLISSE', 7.50, 18.00, 15.50),
            ('POLE QUALITE 1', 7.33, 17.83, 15.33),
            ('POLE QUALITE 2', 7.33, 17.83, 15.33),
            ('RAPHIA 1', 7.33, 17.33, 15.33),
            ('RAPHIA 2', 7.25, 17.25, 15.25),
            ('RAPHIA 3', 7.16, 17.16, 15.16),
            ('RAPHIA 4', 7.25, 17.25, 15.25),
            ('RAPHIA 5', 7.16, 17.16, 15.16),
            ('RAPHIA 6', 7.33, 17.33, 15.33),
            ('RESPONSABLE 0', 7.50, 18.00, 15.50),
            ('RESPONSABLE 1', 7.50, 17.83, 15.50),
            ('RESPONSABLE 2', 7.41, 17.91, 15.41),
            ('RESPONSABLE 3', 7.50, 17.50, 15.50),
            ('RESPONSABLE RAPHIA', 7.33, 17.33, 15.33),
            ('SECURITE', 6.50, 18.00, 18.00),
        ]
        
        created_count = 0
        for section, entree, sortie, samedi in horaires_data:
            obj, created = cls.objects.update_or_create(
                section=section,
                defaults={
                    'heure_entree': entree,
                    'heure_sortie': sortie,
                    'sortie_samedi': samedi
                }
            )
            if created:
                created_count += 1
        
        return created_count
    

class Evenement(models.Model):
    """
    Événements de présence (absences, congés, etc.)
    """
    TYPES_EVENEMENT = [
        ('X', 'Travail normal'),
        ('RM', 'Repos Médical'),
        ('HP', 'Hospitalisation'),
        ('RC', 'Repos de convalescence'),
        ('ANO', 'Absence Non Autorisée'),
        ('CP', 'Congé Payé'),
        ('EF', 'Événement familial'),
        ('F', 'Fonction (délégués)'),
        ('PS', 'Permission Spéciale'),
        ('A', 'Absent'),
    ]
    
    # Utiliser un IntegerField au lieu de ForeignKey car userinfo est managed=False
    userid = models.IntegerField(db_column='userid')
    date = models.DateField()
    type_evenement = models.CharField(
        max_length=3,
        choices=TYPES_EVENEMENT,
        default='X'
    )
    commentaire = models.TextField(blank=True, null=True)
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'evenement'
        unique_together = ['userid', 'date']
        ordering = ['date', 'userid']
        verbose_name = "Événement"
        verbose_name_plural = "Événements"
    
    def __str__(self):
        try:
            user = UserInfo.objects.get(userid=self.userid)
            return f"{user.name} - {self.date} - {self.get_type_evenement_display()}"
        except UserInfo.DoesNotExist:
            return f"User {self.userid} - {self.date} - {self.get_type_evenement_display()}"
    
    @property
    def user(self):
        """Propriété pour accéder à l'objet UserInfo"""
        try:
            return UserInfo.objects.get(userid=self.userid)
        except UserInfo.DoesNotExist:
            return None
    
    @classmethod
    def get_evenement(cls, userid, date):
        """Récupère l'événement pour un utilisateur et une date"""
        try:
            return cls.objects.get(userid=userid, date=date)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def set_evenement(cls, userid, date, type_evenement, commentaire=''):
        """Crée ou met à jour un événement"""
        obj, created = cls.objects.update_or_create(
            userid=userid,
            date=date,
            defaults={
                'type_evenement': type_evenement,
                'commentaire': commentaire
            }
        )
        return obj
    
    @classmethod
    def supprimer_evenement(cls, userid, date):
        """Supprime un événement"""
        try:
            obj = cls.objects.get(userid=userid, date=date)
            obj.delete()
            return True
        except cls.DoesNotExist:
            return False
        

class AnomaliePointage(models.Model):
    """
    Anomalies de pointage (heures modifiées manuellement)
    """
    userid = models.IntegerField(db_column='userid')
    date = models.DateField()
    heure_entree_modifiee = models.TimeField(null=True, blank=True)
    heure_sortie_modifiee = models.TimeField(null=True, blank=True)
    motif = models.TextField(blank=True, null=True)
    modifie_par = models.CharField(max_length=100, blank=True)
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'anomalie_pointage'
        unique_together = ['userid', 'date']
        ordering = ['date', 'userid']
        verbose_name = "Anomalie de pointage"
        verbose_name_plural = "Anomalies de pointage"
    
    def __str__(self):
        try:
            from .models import UserInfo
            user = UserInfo.objects.get(userid=self.userid)
            return f"{user.name} - {self.date}"
        except:
            return f"User {self.userid} - {self.date}"
    
    @property
    def user(self):
        """Propriété pour accéder à l'objet UserInfo"""
        try:
            from .models import UserInfo
            return UserInfo.objects.get(userid=self.userid)
        except:
            return None
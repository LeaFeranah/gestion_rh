from django.db import models
from datetime import date, timedelta, datetime
from calendar import monthrange

class Date(models.Model):
    date = models.DateField(unique=True, primary_key=True)
    code_date = models.CharField(max_length=2)  
    hors_periode = models.BooleanField(default=False)  
    mois_reference = models.DateField()
    est_jour_paiement = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'date'
        ordering = ['date']
    
    def __str__(self):
        if self.est_jour_paiement:
            return f"{self.date} - {self.code_date}P (Jour de paiement)"
        if self.hors_periode:
            return f"{self.date} - {self.code_date}F (Hors période)"
        return f"{self.date} - {self.code_date}"
    
    @property
    def code_affichage(self):
        """Code à afficher : '11P', '11F' ou '11'"""
        if self.est_jour_paiement:
            return f"{self.code_date}P"
        if self.hors_periode:
            return f"{self.code_date}F"
        return self.code_date
    
    @staticmethod
    def get_lundi_precedent(d):
        """Retourne le lundi précédent ou égal à la date donnée"""
        jours_depuis_lundi = d.weekday()  # 0 = lundi, 6 = dimanche
        return d - timedelta(days=jours_depuis_lundi)
    
    @staticmethod
    def calculer_code_date(d, lundi_debut):
        """
        Calcule le code_date pour une date donnée
        d: date à analyser
        lundi_debut: premier lundi de la période
        """
        jours_depuis_debut = (d - lundi_debut).days
        numero_semaine = (jours_depuis_debut // 7) + 1
        jour_semaine = (d.weekday() + 1)  # 1 = lundi, 7 = dimanche
        
        # # Limiter à 5 semaines max
        # if numero_semaine > 5:
        #     numero_semaine = 5
        
        return f"{numero_semaine}{jour_semaine}"
    
    @staticmethod
    def calculer_jours_paiement(annee, mois):
        """
        Calcule les jours de paiement (vendredi et samedi) selon les règles :
        - Si fin du mois précédent = mercredi ou jeudi : vendredi et samedi suivants
        - Si fin du mois précédent = vendredi : ce vendredi et samedi suivant
        - Si fin du mois précédent = samedi, dimanche, lundi ou mardi : vendredi et samedi précédents
        
        Retourne: liste de dates marquées P
        """
        # Trouver le dernier jour du mois PRÉCÉDENT
        if mois == 1:
            mois_precedent = 12
            annee_precedente = annee - 1
        else:
            mois_precedent = mois - 1
            annee_precedente = annee
        
        dernier_jour_mois_precedent = monthrange(annee_precedente, mois_precedent)[1]
        fin_mois_precedent = date(annee_precedente, mois_precedent, dernier_jour_mois_precedent)
        
        jour_semaine_fin = fin_mois_precedent.weekday()  # 0=lundi, 6=dimanche
        
        jours_paiement = []
        
        if jour_semaine_fin == 2:  # Mercredi
            # Vendredi et samedi SUIVANTS
            vendredi = fin_mois_precedent + timedelta(days=2)
            samedi = fin_mois_precedent + timedelta(days=3)
            jours_paiement = [vendredi, samedi]
            
        elif jour_semaine_fin == 3:  # Jeudi
            # Vendredi et samedi SUIVANTS
            vendredi = fin_mois_precedent + timedelta(days=1)
            samedi = fin_mois_precedent + timedelta(days=2)
            jours_paiement = [vendredi, samedi]
            
        elif jour_semaine_fin == 4:  # Vendredi
            # Ce vendredi et samedi suivant
            vendredi = fin_mois_precedent
            samedi = fin_mois_precedent + timedelta(days=1)
            jours_paiement = [vendredi, samedi]
            
        elif jour_semaine_fin in [5, 6, 0, 1]:  # Samedi, Dimanche, Lundi, Mardi
            # Vendredi et samedi PRÉCÉDENTS
            jours_avant_vendredi = {
                5: 1,  # Samedi -> vendredi à -1 jour
                6: 2,  # Dimanche -> vendredi à -2 jours
                0: 3,  # Lundi -> vendredi à -3 jours
                1: 4,  # Mardi -> vendredi à -4 jours
            }
            jours_recul = jours_avant_vendredi[jour_semaine_fin]
            vendredi = fin_mois_precedent - timedelta(days=jours_recul)
            samedi = vendredi + timedelta(days=1)
            jours_paiement = [vendredi, samedi]
        
        return jours_paiement
    
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
        
        # CALCULER LES JOURS DE PAIEMENT
        jours_paiement = cls.calculer_jours_paiement(annee, mois)
        
        # Générer toutes les dates (6 semaines complètes)
        date_courante = lundi_debut
        dates_crees = []
        
        fin_generation = lundi_debut + timedelta(days=6*7-1)  # 6 semaines
        
        while date_courante <= fin_generation:
            # Toujours calculer le code_date
            code = cls.calculer_code_date(date_courante, lundi_debut)
            
            # Déterminer si hors période (F)
            hors_periode = (date_courante < debut_periode or date_courante > fin_periode)
            
            # DÉTERMINER SI JOUR DE PAIEMENT (P)
            est_jour_paiement = date_courante in jours_paiement
            
            obj, created = cls.objects.update_or_create(
                date=date_courante,
                defaults={
                    'code_date': code,
                    'hors_periode': hors_periode,
                    'mois_reference': mois_ref,
                    'est_jour_paiement': est_jour_paiement,
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
    # NOUVEAUX CHAMPS POUR LES JOURS DE PAIEMENT
    sortie_vendredi_paiement = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        default=17.33,
        help_text="Heure de sortie le vendredi de paiement en format décimal"
    )
    sortie_samedi_paiement = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        default=13.00,
        help_text="Heure de sortie le samedi de paiement en format décimal"
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
        if heure_decimal is None:
            return "00:00"
        
        try:
            heure_decimal = float(heure_decimal)
            heures = int(heure_decimal)
            minutes_decimal = (heure_decimal - heures) * 100
            minutes = int(round(minutes_decimal * 0.6))  # Convertir centièmes en minutes
            return f"{heures:02d}:{minutes:02d}"
        except (ValueError, TypeError):
            return "00:00"
    
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
    
    @property
    def sortie_vendredi_paiement_normale(self):
        """Retourne l'heure de sortie vendredi paiement au format HH:MM"""
        return self.decimal_to_time(self.sortie_vendredi_paiement)
    
    @property
    def sortie_samedi_paiement_normale(self):
        """Retourne l'heure de sortie samedi paiement au format HH:MM"""
        return self.decimal_to_time(self.sortie_samedi_paiement)
    
    @classmethod
    def initialiser_horaires(cls):
        """
        Initialise les horaires de toutes les sections
        À appeler une seule fois pour créer les données initiales
        """
        horaires_data = [
            ('ADMINISTRATION', 7.50, 17.83, 15.50, 17.33, 13.00),
            ('BRODERIE MACHINE', 7.50, 18.00, 15.50, 17.50, 13.00),
            ('BRODERIE MAIN AK B', 7.33, 17.33, 15.33, 16.33, 13.00),
            ('BRODERIE MAIN AK17', 7.00, 17.00, 15.00, 16.50, 12.00),
            ('BRODERIE MAIN DEV', 7.50, 18.00, 15.50, 17.50, 13.00),
            ('BUREAU DE METHODE', 7.41, 17.91, 12.00, 17.41, 12.00),
            ('CONTROLE QUALITE AS', 7.50, 17.50, 15.50, 17.00, 13.00),
            ('CHAINE 1', 7.41, 17.91, 15.41, 17.41, 12.91),
            ('CHAINE 2', 7.41, 17.91, 15.41, 17.41, 12.91),
            ('CHAINE 3', 7.41, 17.91, 15.41, 17.41, 12.91),
            ('CHAINE 4', 7.41, 17.91, 15.41, 17.41, 12.91),
            ('CHAINE 5', 7.41, 17.91, 15.41, 17.41, 12.91),
            ('CHAINE 6', 7.41, 17.91, 15.41, 17.41, 12.91),
            ('CHAINE 7', 7.41, 17.91, 15.41, 17.41, 12.91),
            ('CHAINE 8', 7.41, 17.91, 15.41, 17.41, 12.91),
            ('CHAINE 9', 7.41, 17.91, 15.41, 17.41, 12.91),
            ('CHAINE 10', 7.41, 17.91, 15.41, 17.41, 12.91),
            ('CHAINE 11', 7.41, 17.91, 15.41, 17.41, 12.91),
            ('CHAINE 12', 7.41, 17.91, 15.41, 17.41, 12.91),
            ('CHAINE CUIR', 7.41, 17.91, 15.41, 17.33, 12.83),
            ('COLLECTION', 7.50, 17.50, 15.50, 17.50, 13.00),
            ('COUPE', 7.50, 17.50, 15.50, 17.50, 13.00),
            ('COUPE COLLECTION', 7.50, 17.50, 15.50, 17.50, 13.00),
            ('CREATION', 7.00, 17.00, 15.00, 17.00, 12.00),
            ('FINITION D', 7.33, 17.33, 15.33, 17.33, 12.83),
            ('FINITION M', 7.33, 17.33, 15.33, 17.33, 12.83),
            ('FINITION P', 7.33, 17.33, 15.33, 17.33, 12.83),
            ('FINITION Q', 7.33, 17.33, 15.33, 17.33, 12.83),
            ('FINITION R', 7.41, 17.41, 15.41, 17.41, 12.91),
            ('LECTRA', 7.00, 17.00, 12.00, 17.00, 12.00),
            ('LEMARIE HVA', 7.50, 17.50, 15.50, 17.50, 13.00),
            ('MAINTENANCE', 7.50, 17.50, 15.50, 17.50, 13.00),
            ('MAISON', 7.50, 17.50, 15.50, 17.50, 13.00),
            ('MERCHANDISING', 7.00, 17.00, 12.00, 17.00, 12.00),
            ('PACKING/EXPEDITION', 7.50, 18.00, 15.50, 17.50, 13.00),
            ('PLISSE', 7.50, 18.00, 15.50, 17.50, 13.00),
            ('POLE QUALITE 1', 7.33, 17.83, 15.33, 17.33, 12.83),
            ('POLE QUALITE 2', 7.33, 17.83, 15.33, 17.33, 12.83),
            ('RAPHIA 1', 7.33, 17.33, 15.33, 16.83, 12.83),
            ('RAPHIA 2', 7.25, 17.25, 15.25, 16.75, 12.75),
            ('RAPHIA 3', 7.16, 17.16, 15.16, 16.66, 12.66),
            ('RAPHIA 4', 7.25, 17.25, 15.25, 16.75, 12.75),
            ('RAPHIA 5', 7.16, 17.16, 15.16, 16.66, 12.66),
            ('RAPHIA 6', 7.33, 17.33, 15.33, 16.83, 12.83),
            ('RESPONSABLE 0', 7.50, 18.00, 15.50, 17.50, 13.00),
            ('RESPONSABLE 1', 7.50, 17.83, 15.50, 17.33, 13.00),
            ('RESPONSABLE 2', 7.41, 17.91, 15.41, 17.41, 12.91),
            ('RESPONSABLE 3', 7.50, 17.50, 15.50, 17.00, 13.00),
            ('RESPONSABLE RAPHIA', 7.33, 17.33, 15.33, 16.83, 12.83),
            ('SECURITE', 6.50, 18.00, 18.00, 18.00, 18.00),
        ]
        
        created_count = 0
        for section, entree, sortie, samedi, vendredi_paiement, samedi_paiement in horaires_data:
            obj, created = cls.objects.update_or_create(
                section=section,
                defaults={
                    'heure_entree': entree,
                    'heure_sortie': sortie,
                    'sortie_samedi': samedi,
                    'sortie_vendredi_paiement': vendredi_paiement,
                    'sortie_samedi_paiement': samedi_paiement
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
        ('AUT', 'Autre'),
    ]
    
    userid = models.IntegerField(db_column='userid')
    date = models.DateField()
    type_evenement = models.CharField(
        max_length=10,
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


import logging

logger = logging.getLogger(__name__)

class Anomalie(models.Model):
    """
    Modèle pour gérer les anomalies de pointage
    
    Règles de gestion:
    - code_date_brut: heures brutes non modifiables (de CheckInOut)
    - code_date_reel: heures par section (depuis HoraireSection), modifiable
    - code_date_rectifie: heures corrigées manuellement, modifiable
    - etat devient "ok" quand code_date_reel = code_date_rectifie
    """
    
    ETATS_ANOMALIE = [
        ('pas_entree', 'Pas d\'entrée'),
        ('pas_sortie', 'Pas de sortie'),
        ('multiples_pointages', 'Pointages multiples'),
        ('ok', 'OK'),
    ]
    
    userid = models.IntegerField()
    section = models.CharField(max_length=100, null=True, blank=True)
    date = models.DateField()
    code_date = models.CharField(max_length=10, null=True, blank=True)
    
    # Code date BRUT (non modifiable - heures de pointage)
    heure_brute_entree = models.TimeField(null=True, blank=True)
    heure_brute_sortie = models.TimeField(null=True, blank=True)
    
    # Code date REEL (heures par section - modifiable)
    heure_reelle_entree = models.TimeField(null=True, blank=True)
    heure_reelle_sortie = models.TimeField(null=True, blank=True)
    
    # Code date RECTIFIE (heures corrigées - modifiable)
    heure_rectifiee_entree = models.TimeField(null=True, blank=True)
    heure_rectifiee_sortie = models.TimeField(null=True, blank=True)
    
    etat = models.CharField(
        max_length=50,
        choices=ETATS_ANOMALIE,
        default='pas_entree'
    )
    
    commentaire = models.TextField(blank=True, null=True)
    pointages_bruts_json = models.JSONField(   # ← AJOUTER
    null=True, blank=True,
    help_text="Tous les pointages du jour [{time, checktype}, ...]"
    )
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)
    synchronise_le = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'presence_anomalie'
        unique_together = ('userid', 'date')
        ordering = ['-date', 'section', 'userid']
        verbose_name = 'Anomalie'
        verbose_name_plural = 'Anomalies'
    
    def __str__(self):
        return f"Anomalie {self.userid} - {self.date} ({self.etat})"
    
    @property
    def est_corrigee(self):
        """Retourne True si l'anomalie est corrigée (état = ok)"""
        return self.etat == 'ok'
    
    
    # def _determiner_etat(self, ancien_etat=None):
    #     """
    #     Détermine l'état de l'anomalie selon les règles:
    #     - Si pas d'entrée rectifiée → 'pas_entree'
    #     - Si pas de sortie rectifiée → 'pas_sortie'
    #     - Si les deux sont présentes ET égales aux heures réelles → 'ok'
    #     - Sinon → on garde l'ancien état (ou 'pas_entree' par défaut)
    #     """
    #     # CAS 1: Pas d'entrée rectifiée
    #     if not self.heure_rectifiee_entree:
    #         return 'pas_entree'

    #     # CAS 2: Pas de sortie rectifiée
    #     if not self.heure_rectifiee_sortie:
    #         return 'pas_sortie'

    #     # CAS 3: Les deux sont présentes – on vérifie l'égalité avec les heures réelles
    #     if (self.heure_rectifiee_entree == self.heure_reelle_entree and
    #         self.heure_rectifiee_sortie == self.heure_reelle_sortie):
    #         return 'ok'

    #     # Sinon, on conserve l'ancien état s'il existe, sinon 'pas_entree'
    #     return ancien_etat if ancien_etat else 'pas_entree'

    def _determiner_etat(self, ancien_etat=None):
        """
        Détermine l'état de l'anomalie selon les règles.
        Ne touche pas à multiples_pointages si les heures rectifiées sont vides.
        """
        # CAS SPÉCIAL : pointages multiples avec choix manuel pas encore fait
        # → on garde l'état multiples_pointages tant que les rectifiées ne sont pas remplies
        if ancien_etat == 'multiples_pointages':
            if not self.heure_rectifiee_entree or not self.heure_rectifiee_sortie:
                return 'multiples_pointages'

        # CAS 1 : Pas d'entrée rectifiée
        if not self.heure_rectifiee_entree:
            return 'pas_entree'

        # CAS 2 : Pas de sortie rectifiée
        if not self.heure_rectifiee_sortie:
            return 'pas_sortie'

        # CAS 3 : Les deux sont présentes → vérifier égalité avec réelles
        if (self.heure_rectifiee_entree == self.heure_reelle_entree and
                self.heure_rectifiee_sortie == self.heure_reelle_sortie):
            return 'ok'

        # Sinon conserver l'ancien état
        return ancien_etat if ancien_etat else 'pas_entree'
   

    def save(self, *args, **kwargs):
        ancien_etat = self.etat

        # Formater les heures sans secondes
        for field in ['heure_brute_entree', 'heure_brute_sortie',
                    'heure_reelle_entree', 'heure_reelle_sortie',
                    'heure_rectifiee_entree', 'heure_rectifiee_sortie']:
            val = getattr(self, field)
            if val:
                setattr(self, field, self._format_time_without_seconds(val))

        # ─── Auto-complétion depuis les brutes (UNIQUEMENT si le champ est vide) ───
        # On ne force JAMAIS à None : si l'utilisateur a saisi une valeur, on la garde.

        if self.etat == 'multiples_pointages':
            # Rien à copier automatiquement — l'UI propose un choix manuel
            pass

        elif self.etat == 'pas_entree':
            # Sortie brute → rectifiée si vide
            if self.heure_brute_sortie and not self.heure_rectifiee_sortie:
                self.heure_rectifiee_sortie = self.heure_brute_sortie
            # ⚠️ On NE remet PAS heure_rectifiee_entree = None
            # Si l'utilisateur l'a remplie (correction manuelle), on la conserve.

        elif self.etat == 'pas_sortie':
            # Entrée brute → rectifiée si vide
            if self.heure_brute_entree and not self.heure_rectifiee_entree:
                self.heure_rectifiee_entree = self.heure_brute_entree
            # ⚠️ On NE remet PAS heure_rectifiee_sortie = None

        else:
            # Cas normal : copier les deux si vides
            if self.heure_brute_entree and not self.heure_rectifiee_entree:
                self.heure_rectifiee_entree = self.heure_brute_entree
            if self.heure_brute_sortie and not self.heure_rectifiee_sortie:
                self.heure_rectifiee_sortie = self.heure_brute_sortie

        self.etat = self._determiner_etat(ancien_etat)

        if self.etat == 'ok':
            from datetime import datetime
            self.synchronise_le = datetime.now()

        super().save(*args, **kwargs)

    def _format_time_without_seconds(self, time_obj):
        """
        Formate un objet time pour n'avoir que les heures et minutes (secondes à 00)
        """
        from datetime import time
        return time(time_obj.hour, time_obj.minute, 0)

    @classmethod
    def detecter_anomalies_jour(cls, date_jour):
        from .models import CheckInOut, UserInfo, HoraireSection, Date
        from .utils import get_section_employe, decimal_to_time, analyser_pointages_jour

        try:
            date_obj = Date.objects.get(date=date_jour)
        except Date.DoesNotExist:
            logger.warning(f"Date {date_jour} non trouvée")
            return 0

        employes = UserInfo.objects.all()
        count_anomalies = 0

        for employe in employes:
            pointages = CheckInOut.objects.filter(
                user=employe,
                checktime__date=date_jour
            ).order_by('checktime')

            if not pointages.exists():
                cls.objects.filter(userid=employe.userid, date=date_jour).delete()
                continue

            section = get_section_employe(employe.badgenumber)
            try:
                horaire = HoraireSection.objects.get(section=section)
            except HoraireSection.DoesNotExist:
                horaire = HoraireSection.objects.get(section='ADMINISTRATION')

            est_samedi   = date_jour.weekday() == 5
            est_vendredi = date_jour.weekday() == 4
            est_paiement = date_obj.est_jour_paiement

            heure_reelle_entree = decimal_to_time(horaire.heure_entree)
            if est_paiement and est_vendredi:
                heure_reelle_sortie = decimal_to_time(horaire.sortie_vendredi_paiement)
            elif est_paiement and est_samedi:
                heure_reelle_sortie = decimal_to_time(horaire.sortie_samedi_paiement)
            elif est_samedi:
                heure_reelle_sortie = decimal_to_time(horaire.sortie_samedi)
            else:
                heure_reelle_sortie = decimal_to_time(horaire.heure_sortie)

            pointages_list = list(pointages)
            tries = sorted(pointages_list, key=lambda p: p.checktime)

            # ── Heures brutes basées sur le checktype réel ─────────────────────
            entrees_brutes = [p for p in tries if p.checktype.upper() == 'O']
            sorties_brutes  = [p for p in tries if p.checktype.upper() == 'I']
            heure_brute_entree = entrees_brutes[0].checktime.time() if entrees_brutes else None
            heure_brute_sortie = sorties_brutes[-1].checktime.time() if sorties_brutes else None

            # ── Analyse ────────────────────────────────────────────────────────
            heure_entree_calc, heure_sortie_calc, type_anomalie, liste_bruts = analyser_pointages_jour(
                pointages_list, heure_reelle_entree, heure_reelle_sortie, seuil_minutes=30,
            )

            # ── Déterminer état et heures rectifiées ───────────────────────────
            if type_anomalie == 'multiples_pointages':
                etat                   = 'multiples_pointages'
                heure_rectifiee_entree = None
                heure_rectifiee_sortie = None

            elif type_anomalie == 'pas_entree':
                etat                   = 'pas_entree'
                heure_rectifiee_entree = None
                heure_rectifiee_sortie = heure_sortie_calc

            elif type_anomalie == 'pas_sortie':
                etat                   = 'pas_sortie'
                heure_rectifiee_entree = heure_entree_calc
                heure_rectifiee_sortie = None

            elif heure_entree_calc is None:
                etat                   = 'pas_entree'
                heure_rectifiee_entree = None
                heure_rectifiee_sortie = heure_sortie_calc

            elif heure_sortie_calc is None:
                etat                   = 'pas_sortie'
                heure_rectifiee_entree = heure_entree_calc
                heure_rectifiee_sortie = None

            else:
                etat                   = 'ok'
                heure_rectifiee_entree = heure_entree_calc
                heure_rectifiee_sortie = heure_sortie_calc

            defaults = {
                'section':                section,
                'code_date':              date_obj.code_date,
                'heure_brute_entree':     heure_brute_entree,
                'heure_brute_sortie':     heure_brute_sortie,
                'heure_reelle_entree':    heure_reelle_entree,
                'heure_reelle_sortie':    heure_reelle_sortie,
                'heure_rectifiee_entree': heure_rectifiee_entree,
                'heure_rectifiee_sortie': heure_rectifiee_sortie,
                'pointages_bruts_json':   liste_bruts,
                'etat':                   etat,
                'commentaire':            '',
            }

            anomalie, created = cls.objects.update_or_create(
                userid=employe.userid,
                date=date_jour,
                defaults=defaults,
            )
            if created:
                count_anomalies += 1

            if etat == 'ok':
                anomalie.delete()
                if created:
                    count_anomalies -= 1

        return count_anomalies
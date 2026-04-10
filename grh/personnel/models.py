from django.db import models
from django.core.validators import FileExtensionValidator
from datetime import date
from django.conf import settings
from django.utils import timezone


class TimeStampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class InformationPersonnelle(TimeStampModel):
    
    SEXE_CHOICES = [
        ('Masculin', 'Masculin'),
        ('Féminin', 'Féminin'),
        ('MASCULIN','MASCULIN'),
        ('FEMININ','FEMININ'),
        ('FÉMININ','FÉMININ')
    ]

    numero_matricule = models.CharField(max_length=50, unique=True)
    nom_complet = models.CharField(max_length=255)
    sexe = models.CharField(max_length=10, choices=SEXE_CHOICES, null=True, blank=True)
    appellation = models.CharField(max_length=100, null=True, blank=True)
    date_naissance = models.DateField(null=True, blank=True)
    lieu_naissance = models.CharField(max_length=100, null=True, blank=True)
    CIN = models.CharField(max_length=50, null=True, blank=True)
    date_CIN = models.DateField(null=True, blank=True)
    lieu_CIN = models.CharField(max_length=100, null=True, blank=True)
    ancien_numero_journaliere = models.CharField(max_length=50, null=True, blank=True)
    pere = models.CharField(max_length=100, null=True, blank=True)
    mere = models.CharField(max_length=100, null=True, blank=True)
    adresse = models.TextField(null=True, blank=True)
    telephone = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    depart = models.CharField(max_length=100, null=True, blank=True)
    
    # 🔹 DUPLICATA CIN
    date_duplicata = models.DateField(null=True, blank=True, verbose_name="Date du duplicata")
    lieu_duplicata = models.CharField(max_length=100, null=True, blank=True, verbose_name="Lieu du duplicata")
    
    # 🔹 PASSPORT
    code_pays_passport = models.CharField(max_length=3, null=True, blank=True, verbose_name="Code pays", help_text="Code pays du passport (ex: MDG, FRA)")
    type_passport = models.CharField(max_length=20, null=True, blank=True, verbose_name="Type de passport", help_text="Type de passport (ex: Ordinaire, Diplomatique)")
    numero_passport = models.CharField(max_length=50, null=True, blank=True, verbose_name="Numéro de passport")
    date_expiration_passport = models.DateField(null=True, blank=True, verbose_name="Date d'expiration du passport")
    
    # 🔹 PERMIS DE CONDUIRE - Catégories avec dates
    permis_categorie_a = models.DateField(null=True, blank=True, verbose_name="Permis Catégorie A", help_text="Date d'obtention du permis A")
    permis_categorie_b = models.DateField(null=True, blank=True, verbose_name="Permis Catégorie B", help_text="Date d'obtention du permis B")
    permis_categorie_c = models.DateField(null=True, blank=True, verbose_name="Permis Catégorie C", help_text="Date d'obtention du permis C")
    permis_categorie_d = models.DateField(null=True, blank=True, verbose_name="Permis Catégorie D", help_text="Date d'obtention du permis D")
    permis_categorie_e = models.DateField(null=True, blank=True, verbose_name="Permis Catégorie E", help_text="Date d'obtention du permis E")
    permis_categorie_f = models.DateField(null=True, blank=True, verbose_name="Permis Catégorie F", help_text="Date d'obtention du permis F")
    
    # 🔹 NOUVEAU : Lien avec l'utilisateur RH qui a créé l'employé
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='employes_crees',
        null=True,
        blank=True
    )

    # 🔹 Photo de l'employé
    photo = models.ImageField(
        upload_to='photos_employes/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )

    # 🔹 Paramètres pour suivre la photo
    photo_taille = models.PositiveIntegerField(null=True, blank=True, help_text="Taille du fichier en octets")
    photo_type = models.CharField(max_length=10, null=True, blank=True, help_text="Extension du fichier")
    photo_largeur = models.PositiveIntegerField(null=True, blank=True, help_text="Largeur en pixels")
    photo_hauteur = models.PositiveIntegerField(null=True, blank=True, help_text="Hauteur en pixels")
    photo_validee = models.BooleanField(default=False, help_text="Statut de validation de la photo")

    def __str__(self):
        return f"{self.numero_matricule} - {self.nom_complet}"
    
    @property
    def age(self):
        """Calcule l'âge automatiquement à partir de la date de naissance"""
        if self.date_naissance:
            today = date.today()
            age = today.year - self.date_naissance.year - (
                (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day)
            )
            return age
        return None
    
    @property
    def retraite(self):
        """Détermine si l'employé est à la retraite (≥ 60 ans)"""
        age = self.age
        if age is not None:
            return "Oui" if age >= 60 else "Non"
        return "Non spécifié"
    
    @property
    def passport_valide(self):
        """Vérifie si le passport est encore valide"""
        if self.date_expiration_passport:
            return date.today() <= self.date_expiration_passport
        return None
    
    @property
    def categories_permis(self):
        """Retourne la liste des catégories de permis obtenues"""
        categories = []
        if self.permis_categorie_a:
            categories.append('A')
        if self.permis_categorie_b:
            categories.append('B')
        if self.permis_categorie_c:
            categories.append('C')
        if self.permis_categorie_d:
            categories.append('D')
        if self.permis_categorie_e:
            categories.append('E')
        if self.permis_categorie_f:
            categories.append('F')
        return categories
    
    def save(self, *args, **kwargs):
        if self.photo:
            self.photo_taille = self.photo.size
            self.photo_type = self.photo.name.split('.')[-1].lower()
            from PIL import Image
            img = Image.open(self.photo)
            self.photo_largeur, self.photo_hauteur = img.size
        super().save(*args, **kwargs)


class DossierPersonnel(TimeStampModel):
    employe = models.OneToOneField(InformationPersonnelle, on_delete=models.CASCADE, related_name='dossier_personnel')
    cv = models.FileField(upload_to='dossiers/cv/',null=True,blank=True,validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])])
    lettre_motivation = models.FileField(upload_to='dossiers/lettres/',null=True,blank=True,validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])])
    residence = models.FileField(upload_to='dossiers/residences/',null=True,blank=True,validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])])
    cin = models.FileField(upload_to='dossiers/cin/',null=True,blank=True,validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])])
    carte_cnaps = models.FileField(upload_to='dossiers/cnaps/',null=True,blank=True,validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])])
    rib = models.FileField(upload_to='dossiers/rib/',null=True,blank=True,validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])])
    photo_identite = models.FileField(upload_to='dossiers/photos/',null=True,blank=True,validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])])
    certificat_travail = models.FileField(upload_to='dossiers/certificats/',null=True,blank=True,validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])])
    
    def __str__(self):
        return f"Dossier de {self.employe.nom_complet}"


class InformationBancaire(TimeStampModel):
    employe = models.OneToOneField(InformationPersonnelle, on_delete=models.CASCADE, related_name='bancaire')
    nom_banque = models.CharField(max_length=100, null=True, blank=True)
    cle_rib = models.CharField(max_length=100, null=True, blank=True)


class InformationSociale(TimeStampModel):
    employe = models.OneToOneField(InformationPersonnelle, on_delete=models.CASCADE, related_name='sociale')
    retraite = models.CharField(max_length=50, null=True, blank=True)
    enfant_allocation = models.IntegerField(default=0, null=True, blank=True)


class InformationFamiliale(TimeStampModel):
    employe = models.OneToOneField(InformationPersonnelle, on_delete=models.CASCADE, related_name='familiale')
    epoux_nom = models.CharField(max_length=100, null=True, blank=True)
    epoux_prenoms = models.CharField(max_length=100, null=True, blank=True)
    epoux_date_naissance = models.DateField(null=True, blank=True)
    epoux_lieu_naissance = models.CharField(max_length=100, null=True, blank=True)
    epoux_societe = models.CharField(max_length=150, null=True, blank=True)
    epoux_fonction = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Famille de {self.employe.nom_complet}"


class Enfant(TimeStampModel):
    familiale = models.ForeignKey(InformationFamiliale, on_delete=models.CASCADE, related_name='enfants')
    nom_prenoms = models.CharField(max_length=150)
    sexe = models.CharField(
        max_length=10, 
        choices=[('Masculin', 'Masculin'), ('Féminin', 'Féminin')],
        null=True,        
        blank=True,       
    )
    date_naissance = models.DateField(null=True, blank=True)
    lieu_naissance = models.CharField(max_length=100, null=True, blank=True)

    @property
    def age(self):
        if self.date_naissance:
            today = date.today()
            return today.year - self.date_naissance.year - (
                (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day)
            )
        return None

    def __str__(self):
        sexe_display = self.sexe if self.sexe else "Non spécifié"
        age_display = f"{self.age} ans" if self.age is not None else "Âge non disponible"
        return f"{self.nom_prenoms} ({sexe_display}, {age_display})"


class InformationProfessionnelle(TimeStampModel):
    CATEGORIE_CHOICES = [
        ('M1', 'M1'),
        ('M2', 'M2'),
        ('0S1', '0S1'),
        ('0S2', '0S2'),
        ('0S3', '0S3'),
        ('0P1A', '0P1A'),
        ('0P1B', '0P1B'),
        ('0P2A', '0P2A'),
        ('0P2B', '0P2B'),
        ('0P3', '0P3'),
        ('H.C', 'H.C'),
    ]

    

    RESPONSABLE_CHOICES = [
        ('', 'Sélectionnez un responsable'),
        ('RESPONSABLE 0', 'Responsable 0'),
        ('RESPONSABLE 1', 'Responsable 1'),
        ('RESPONSABLE 2', 'Responsable 2'),
        ('RESPONSABLE 3', 'Responsable 3'),
        ('RESPONSABLE RAPHIA', 'Responsable Raphia'),
    ]

    employe = models.OneToOneField(InformationPersonnelle, on_delete=models.CASCADE, related_name='information_professionnelle')
    date_embauche = models.DateField(null=True, blank=True,help_text="Date d'embauche de l'employé")
    fonction = models.CharField(max_length=100, null=True, blank=True,help_text="Fonction ou poste occupé")
    section = models.CharField(max_length=50, null=True, blank=True,help_text="Section/département de l'employé")
    categorie = models.CharField(max_length=10, choices=CATEGORIE_CHOICES, null=True, blank=True,help_text="Catégorie professionnelle de l'employé")
    responsable = models.CharField(max_length=100, choices=RESPONSABLE_CHOICES, null=True, blank=True)
    responsable_section = models.CharField(max_length=100, null=True, blank=True,help_text="Nom du responsable de la section")
    numero_cnaps = models.CharField(max_length=50, null=True, blank=True,help_text="Numéro CNAPS (Caisse Nationale de Prévoyance Sociale)",verbose_name="Numéro CNAPS")
    numero_ostie = models.CharField(max_length=50, null=True, blank=True,help_text="Numéro OSTIE (Organisme de Santé et de Travail pour les Indépendants et Employés)",verbose_name="Numéro OSTIE")
    section_ref = models.ForeignKey(
        'presence.Section',          # référence cross-app
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='info_pro',
        verbose_name="Section (référence)",
        help_text="Section issue de db_section, calculée automatiquement",
    )
    def __str__(self):
        return f"Info Pro - {self.employe.nom_complet}"
    
    def save(self, *args, **kwargs):
        """Autorise la création initiale mais bloque les modifications directes des champs sensibles
        SAUF si c'est via une évolution de poste"""
        is_new = self.pk is None
        
        # Si c'est une sauvegarde via une évolution de poste, on autorise
        if hasattr(self, '_modification_via_evolution') and self._modification_via_evolution:
            # Supprimer l'attribut pour les prochaines sauvegardes
            delattr(self, '_modification_via_evolution')
            super().save(*args, **kwargs)
            return
        
        if not is_new:
            # Pour les mises à jour, récupérer l'instance originale
            original = InformationProfessionnelle.objects.get(pk=self.pk)
            
            # Liste des champs sensibles qui ne peuvent pas être modifiés directement
            champs_sensibles = ['categorie', 'fonction', 'section', 'responsable']
            modifications_detectees = False
            
            for champ in champs_sensibles:
                original_value = getattr(original, champ)
                nouvelle_valeur = getattr(self, champ)
                
                # Vérifier si le champ a été modifié
                if original_value != nouvelle_valeur:
                    modifications_detectees = True
                    # Revenir à l'ancienne valeur
                    setattr(self, champ, original_value)
            
            if modifications_detectees:
                raise ValueError(
                    "Les champs 'categorie', 'fonction', 'section' et 'responsable' "
                    "ne peuvent pas être modifiés directement. "
                    "Utilisez le système d'évolution de poste."
                )
        
        super().save(*args, **kwargs)

class EvolutionPoste(TimeStampModel):
    """Modèle pour gérer les évolutions de poste manuellement"""
    
    STATUT_CHOICES = [
        ('PROPOSEE', 'Proposée'),
        ('APPROUVEE', 'Approuvée'),
        ('REALISEE', 'Réalisée'),
        ('ANNULEE', 'Annulée'),
    ]
    
    employe = models.ForeignKey(
        InformationPersonnelle, 
        on_delete=models.CASCADE, 
        related_name='evolutions_poste'
    )
    
    # Anciennes valeurs (capturées automatiquement lors de la création)
    ancienne_categorie = models.CharField(max_length=10, choices=InformationProfessionnelle.CATEGORIE_CHOICES, null=True, blank=True)
    ancienne_fonction = models.CharField(max_length=100, null=True, blank=True)
    ancienne_section = models.CharField(max_length=50, null=True, blank=True)
    ancien_responsable = models.CharField(max_length=100, choices=InformationProfessionnelle.RESPONSABLE_CHOICES, null=True, blank=True)
    
    # Nouvelles valeurs (saisies par l'utilisateur)
    nouvelle_categorie = models.CharField(max_length=10, choices=InformationProfessionnelle.CATEGORIE_CHOICES)
    nouvelle_fonction = models.CharField(max_length=100)
    nouvelle_section = models.CharField(max_length=50)
    nouveau_responsable = models.CharField(max_length=100, choices=InformationProfessionnelle.RESPONSABLE_CHOICES, null=True, blank=True)
    
    # Informations sur l'évolution
    date_evolution = models.DateField(help_text="Date effective de l'évolution de poste")
    motif = models.TextField(help_text="Motif ou raison du changement de poste")
    commentaire = models.TextField(null=True, blank=True)
    
    # Qui a effectué le changement
    modifie_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='evolutions_poste_effectuees'
    )
    
    # Statut
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='PROPOSEE'
    )
    
    class Meta:
        ordering = ['-date_evolution', '-created_at']
        verbose_name = "Évolution de poste"
        verbose_name_plural = "Évolutions de poste"
    
    def __str__(self):
        return f"Évolution - {self.employe.nom_complet} - {self.date_evolution}"
    
    def appliquer_evolution(self):
        """Applique l'évolution en mettant à jour l'InformationProfessionnelle"""
        try:
            info_pro = InformationProfessionnelle.objects.get(employe=self.employe)
            
            # Mettre à jour avec les nouvelles valeurs
            info_pro.categorie = self.nouvelle_categorie
            info_pro.fonction = self.nouvelle_fonction
            info_pro.section = self.nouvelle_section
            if self.nouveau_responsable:
                info_pro.responsable = self.nouveau_responsable
            
            # Ajouter un flag pour indiquer que c'est une modification via évolution
            info_pro._modification_via_evolution = True
            
            info_pro.save()
            self.statut = 'REALISEE'
            self.save()
            
            return True
        except InformationProfessionnelle.DoesNotExist:
            print(f"❌ L'employé {self.employe.nom_complet} n'a pas d'information professionnelle")
            return False
        except Exception as e:
            print(f"❌ Erreur lors de l'application de l'évolution: {str(e)}")
            raise  # Relancer l'exception pour le logging


class InformationSalairePersonnel(TimeStampModel):
    employe = models.OneToOneField('InformationPersonnelle', on_delete=models.CASCADE, related_name='salaire_personnel')
    
    @property
    def categorie(self):
        """Récupère la catégorie depuis InformationProfessionnelle en lecture seule"""
        try:
            if hasattr(self.employe, 'information_professionnelle'):
                return self.employe.information_professionnelle.categorie
        except:
            pass
        return None
    
    @categorie.setter
    def categorie(self, value):
        """Empêche la modification directe de la catégorie"""
        raise AttributeError("La catégorie ne peut pas être modifiée directement. Utilisez InformationProfessionnelle.categorie à la place.")
    
    indice = models.CharField(max_length=20, null=True, blank=True, help_text="Indice de l'employé")
    taux_horaire = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Taux horaire en Ariary")
    salaire_base = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Salaire de base en Ariary")
    autre_indemnite = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Autres indemnités en Ariary")
    prime_anciennete = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    indemnite_deplacement = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    dernier_aug_indice = models.CharField(max_length=50, null=True, blank=True)
    salaire_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Salaire total calculé en Ariary")

    def __str__(self):
        return f"Salaire de {self.employe.nom_complet}"


class HistoriqueSalaire(TimeStampModel):
    ACTION_CHOICES = [
        ('CREATE', 'Création'),
        ('UPDATE', 'Modification'),
    ]
    
    employe = models.ForeignKey(InformationPersonnelle, on_delete=models.CASCADE, related_name='historiques_salaire')
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    
    modifie_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='modifications_salaire'
    )
    ancienne_categorie = models.CharField(max_length=10, null=True, blank=True)
    ancienne_indice = models.CharField(max_length=20, null=True, blank=True)
    ancien_taux_horaire = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ancien_salaire_base = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    ancienne_autre_indemnite = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    ancienne_prime_anciennete = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    ancienne_indemnite_deplacement = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    ancien_salaire_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    nouvelle_categorie = models.CharField(max_length=10, null=True, blank=True)
    nouvelle_indice = models.CharField(max_length=20, null=True, blank=True)
    nouveau_taux_horaire = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    nouveau_salaire_base = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    nouvelle_autre_indemnite = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    nouvelle_prime_anciennete = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    nouvelle_indemnite_deplacement = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    nouveau_salaire_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    commentaire = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Historique de salaire"
        verbose_name_plural = "Historiques de salaire"
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.employe.nom_complet} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"
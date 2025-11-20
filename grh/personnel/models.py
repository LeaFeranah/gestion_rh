# # from django.db import models
# # from django.utils import timezone

# # # Model de base pour timestamp (création / mise à jour)
# # class TimeStampModel(models.Model):
# #     created_at = models.DateTimeField(auto_now_add=True)
# #     updated_at = models.DateTimeField(auto_now=True)

# #     class Meta:
# #         abstract = True

# # # Model Employé (table principale)
# # class Employe(TimeStampModel):
# #     matricule = models.CharField(max_length=20, unique=True)
# #     nom = models.CharField(max_length=50)
# #     prenoms = models.CharField(max_length=100)
# #     fonction = models.CharField(max_length=100)
# #     section = models.CharField(max_length=100)
# #     appelation = models.CharField(max_length=100)
# #     email = models.EmailField(blank=True, null=True)
# #     telephone = models.CharField(max_length=20, blank=True, null=True)

# #     def __str__(self):
# #         return f"{self.matricule} - {self.nom} {self.prenoms}"

# # # Informations sur le poste
# # class Poste(TimeStampModel):
# #     employe = models.OneToOneField(Employe, on_delete=models.CASCADE, related_name='poste')
# #     titre_poste = models.CharField(max_length=100)
# #     date_embauche = models.DateField()
# #     type_contrat = models.CharField(max_length=50, choices=[('CDD','CDD'), ('CDI','CDI')])
# #     salaire = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

# # # Informations bancaires
# # class Banque(TimeStampModel):
# #     employe = models.OneToOneField(Employe, on_delete=models.CASCADE, related_name='banque')
# #     nom_banque = models.CharField(max_length=100)
# #     numero_compte = models.CharField(max_length=50)
# #     iban = models.CharField(max_length=34, blank=True, null=True)

# # # Informations sociales
# # class Social(TimeStampModel):
# #     employe = models.OneToOneField(Employe, on_delete=models.CASCADE, related_name='social')
# #     num_cnaps = models.CharField(max_length=50, blank=True, null=True)
# #     num_ostie = models.CharField(max_length=50, blank=True, null=True)
# #     assurance_sante = models.CharField(max_length=100, blank=True, null=True)

# # # Pièces d'identité
# # class Identite(TimeStampModel):
# #     employe = models.OneToOneField(Employe, on_delete=models.CASCADE, related_name='identite')
# #     num_carte_identite = models.CharField(max_length=50)
# #     date_naissance = models.DateField()
# #     lieu_naissance = models.CharField(max_length=100)
# #     adresse = models.TextField()

# # # Documents de l'employé (plusieurs fichiers possibles)
# # class Document(TimeStampModel):
# #     employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='documents')
# #     type_document = models.CharField(max_length=50, choices=[
# #         ('CV', 'CV'), 
# #         ('Contrat', 'Contrat'), 
# #         ('Lettre', 'Lettre de motivation'), 
# #         ('Autre', 'Autre')
# #     ])
# #     fichier = models.FileField(upload_to='documents_employes/')
# #     date_ajout = models.DateTimeField(default=timezone.now)








# # from django.db import models

# # class TimeStampModel(models.Model):
# #     created_at = models.DateTimeField(auto_now_add=True)
# #     updated_at = models.DateTimeField(auto_now=True)

# #     class Meta:
# #         abstract = True

# # class InformationPersonnelle(TimeStampModel):
# #     numero_matricule = models.CharField(max_length=50, unique=True)
# #     nom = models.CharField(max_length=100)
# #     prenoms = models.CharField(max_length=100)
# #     sexe = models.CharField(max_length=10)
# #     date_naissance = models.DateField(null=True, blank=True)
# #     lieu_naissance = models.CharField(max_length=100, null=True, blank=True)
# #     CIN = models.CharField(max_length=50, null=True, blank=True)
# #     date_lieu_CIN = models.CharField(max_length=100, null=True, blank=True)
# #     pere = models.CharField(max_length=100, null=True, blank=True)
# #     mere = models.CharField(max_length=100, null=True, blank=True)
# #     adresse = models.TextField(null=True, blank=True)
# #     telephone = models.CharField(max_length=50, null=True, blank=True)
# #     email = models.EmailField(null=True, blank=True)
# #     mobile_money = models.CharField(max_length=50, null=True, blank=True)
# #     photo = models.ImageField(upload_to='photos/', null=True, blank=True)
# #     photo_1 = models.ImageField(upload_to='photos/', null=True, blank=True)

# #     def __str__(self):
# #         return f"{self.numero_matricule} - {self.nom} {self.prenoms}"

# # class InformationProfessionnelle(TimeStampModel):
# #     employe = models.OneToOneField(InformationPersonnelle, on_delete=models.CASCADE, related_name='professionnelle')
# #     fonction = models.CharField(max_length=100)
# #     section = models.CharField(max_length=100, null=True, blank=True)
# #     appellation = models.CharField(max_length=100, null=True, blank=True)
# #     date_embauche = models.DateField(null=True, blank=True)
# #     date_debauche = models.DateField(null=True, blank=True)
# #     ancien_numero = models.CharField(max_length=50, null=True, blank=True)
# #     titre_poste = models.CharField(max_length=100, null=True, blank=True)
# #     departement = models.CharField(max_length=100, null=True, blank=True)
# #     secteur = models.CharField(max_length=100, null=True, blank=True)
# #     code_fonction = models.CharField(max_length=50, null=True, blank=True)
# #     section_temporaraire = models.CharField(max_length=100, null=True, blank=True)
# #     pour_responsable = models.CharField(max_length=100, null=True, blank=True)
# #     depart = models.CharField(max_length=100, null=True, blank=True)
# #     motif_depart = models.TextField(null=True, blank=True)

# # class InformationBancaire(TimeStampModel):
# #     employe = models.OneToOneField(InformationPersonnelle, on_delete=models.CASCADE, related_name='bancaire')
# #     nom_banque = models.CharField(max_length=100)
# #     code_banque = models.CharField(max_length=50)
# #     code_agence = models.CharField(max_length=50)
# #     numero_compte = models.CharField(max_length=50)
# #     cle_rib = models.CharField(max_length=10)
# #     banque_beneficiaire = models.CharField(max_length=100, null=True, blank=True)

# # class InformationSociale(TimeStampModel):
# #     employe = models.OneToOneField(InformationPersonnelle, on_delete=models.CASCADE, related_name='sociale')
# #     numero_cnaps = models.CharField(max_length=50, null=True, blank=True)
# #     retraite = models.CharField(max_length=50, null=True, blank=True)
# #     enfant_allocation = models.IntegerField(default=0)

# # class InformationComplementaire(TimeStampModel):
# #     employe = models.OneToOneField(InformationPersonnelle, on_delete=models.CASCADE, related_name='complementaire')
# #     note = models.TextField(null=True, blank=True)
# #     maison = models.CharField(max_length=100, null=True, blank=True)
# #     contact_rapide = models.CharField(max_length=100, null=True, blank=True)
# #     dernier_aug_indice = models.CharField(max_length=50, null=True, blank=True)
# #     pour_30 = models.CharField(max_length=50, null=True, blank=True)
# #     T1_17 = models.CharField(max_length=50, null=True, blank=True)
# #     obs_prime = models.TextField(null=True, blank=True)
# #     enquete = models.TextField(null=True, blank=True)
# #     categorie = models.CharField(max_length=50, null=True, blank=True)





# from django.db import models

# class TimeStampModel(models.Model):
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         abstract = True


# # class InformationPersonnelle(TimeStampModel):
# #     numero_matricule = models.CharField(max_length=50, unique=True)
# #     nom = models.CharField(max_length=100)
# #     prenoms = models.CharField(max_length=100)
# #     sexe = models.CharField(max_length=10, null=True, blank=True)
# #     date_naissance = models.DateField(null=True, blank=True)
# #     lieu_naissance = models.CharField(max_length=100, null=True, blank=True)
# #     CIN = models.CharField(max_length=50, null=True, blank=True)
# #     date_lieu_CIN = models.CharField(max_length=100, null=True, blank=True)
# #     pere = models.CharField(max_length=100, null=True, blank=True)
# #     mere = models.CharField(max_length=100, null=True, blank=True)
# #     adresse = models.TextField(null=True, blank=True)
# #     telephone = models.CharField(max_length=50, null=True, blank=True)
# #     email = models.EmailField(null=True, blank=True)
# #     mobile_money = models.CharField(max_length=50, null=True, blank=True)
# #     photo = models.ImageField(upload_to='photos/', null=True, blank=True)
# #     photo_1 = models.ImageField(upload_to='photos/', null=True, blank=True)

# #     def __str__(self):
# #         return f"{self.numero_matricule} - {self.nom} {self.prenoms}"


# class InformationPersonnelle(TimeStampModel):
#     SEXE_CHOICES = [
#         ('Masculin', 'Masculin'),
#         ('Féminin', 'Féminin'),
#     ]

#     numero_matricule = models.CharField(max_length=50, unique=True)
#     nom = models.CharField(max_length=100)
#     prenoms = models.CharField(max_length=100)
#     sexe = models.CharField(max_length=10, choices=SEXE_CHOICES, null=True, blank=True)
#     appellation = models.CharField(max_length=100, null=True, blank=True)
#     section = models.CharField(max_length=100, null=True, blank=True)
#     fonction = models.CharField(max_length=100, null=True, blank=True)
#     date_naissance = models.DateField(null=True, blank=True)
#     lieu_naissance = models.CharField(max_length=100, null=True, blank=True)
#     CIN = models.CharField(max_length=50, null=True, blank=True)
#     date_lieu_CIN = models.CharField(max_length=100, null=True, blank=True)
#     pere = models.CharField(max_length=100, null=True, blank=True)
#     mere = models.CharField(max_length=100, null=True, blank=True)
#     adresse = models.TextField(null=True, blank=True)
#     telephone = models.CharField(max_length=50, null=True, blank=True)
#     email = models.EmailField(null=True, blank=True)
#     mobile_money = models.CharField(max_length=50, null=True, blank=True)
#     photo = models.ImageField(upload_to='photos/', null=True, blank=True)
#     photo_1 = models.ImageField(upload_to='photos/', null=True, blank=True)

#     def __str__(self):
#         return f"{self.numero_matricule} - {self.nom} {self.prenoms}"


# class InformationProfessionnelle(TimeStampModel):
#     employe = models.OneToOneField(InformationPersonnelle, on_delete=models.CASCADE, related_name='professionnelle')
#     #fonction = models.CharField(max_length=100, null=True, blank=True)
#     #section = models.CharField(max_length=100, null=True, blank=True)
#     #appellation = models.CharField(max_length=100, null=True, blank=True)
#     date_embauche = models.DateField(null=True, blank=True)
#     date_debauche = models.DateField(null=True, blank=True)
#     ancien_numero = models.CharField(max_length=50, null=True, blank=True)
#     titre_poste = models.CharField(max_length=100, null=True, blank=True)
#     departement = models.CharField(max_length=100, null=True, blank=True)
#     secteur = models.CharField(max_length=100, null=True, blank=True)
#     code_fonction = models.CharField(max_length=50, null=True, blank=True)
#     section_temporaire = models.CharField(max_length=100, null=True, blank=True)
#     pour_responsable = models.CharField(max_length=100, null=True, blank=True)
#     depart = models.CharField(max_length=100, null=True, blank=True)
#     motif_depart = models.TextField(null=True, blank=True)


# class InformationBancaire(TimeStampModel):
#     employe = models.OneToOneField(InformationPersonnelle, on_delete=models.CASCADE, related_name='bancaire')
#     nom_banque = models.CharField(max_length=100, null=True, blank=True)
#     code_banque = models.CharField(max_length=50, null=True, blank=True)
#     code_agence = models.CharField(max_length=50, null=True, blank=True)
#     numero_compte = models.CharField(max_length=50, null=True, blank=True)
#     cle_rib = models.CharField(max_length=10, null=True, blank=True)
#     banque_beneficiaire = models.CharField(max_length=100, null=True, blank=True)


# class InformationSociale(TimeStampModel):
#     employe = models.OneToOneField(InformationPersonnelle, on_delete=models.CASCADE, related_name='sociale')
#     numero_cnaps = models.CharField(max_length=50, null=True, blank=True)
#     retraite = models.CharField(max_length=50, null=True, blank=True)
#     enfant_allocation = models.IntegerField(default=0, null=True, blank=True)


# class InformationComplementaire(TimeStampModel):
#     employe = models.OneToOneField(InformationPersonnelle, on_delete=models.CASCADE, related_name='complementaire')
#     note = models.TextField(null=True, blank=True)
#     maison = models.CharField(max_length=100, null=True, blank=True)
#     contact_rapide = models.CharField(max_length=100, null=True, blank=True)
#     dernier_aug_indice = models.CharField(max_length=50, null=True, blank=True)
#     pour_30 = models.CharField(max_length=50, null=True, blank=True)
#     T1_17 = models.CharField(max_length=50, null=True, blank=True)
#     obs_prime = models.TextField(null=True, blank=True)
#     enquete = models.TextField(null=True, blank=True)
#     categorie = models.CharField(max_length=50, null=True, blank=True)


from django.db import models
from django.core.validators import FileExtensionValidator
from datetime import date
from django.conf import settings


class TimeStampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True




# class InformationPersonnelle(TimeStampModel):
    
#     SEXE_CHOICES = [
#         ('Masculin', 'Masculin'),
#         ('Féminin', 'Féminin'),
#     ]

#     numero_matricule = models.CharField(max_length=50, unique=True)
#     nom = models.CharField(max_length=100)
#     prenoms = models.CharField(max_length=100)
#     sexe = models.CharField(max_length=10, choices=SEXE_CHOICES, null=True, blank=True)
#     appellation = models.CharField(max_length=100, null=True, blank=True)
#     section = models.CharField(max_length=100, null=True, blank=True)
#     fonction = models.CharField(max_length=100, null=True, blank=True)
#     date_naissance = models.DateField(null=True, blank=True)
#     lieu_naissance = models.CharField(max_length=100, null=True, blank=True)
#     CIN = models.CharField(max_length=50, null=True, blank=True)
#     date_CIN = models.DateField(null=True, blank=True)
#     lieu_CIN=models.CharField(max_length=100, null=True, blank=True)
#     numero_cnaps = models.CharField(max_length=50, null=True, blank=True)
#     ancien_numero_journaliere = models.CharField(max_length=50, null=True, blank=True)
#     pere = models.CharField(max_length=100, null=True, blank=True)
#     mere = models.CharField(max_length=100, null=True, blank=True)
#     adresse = models.TextField(null=True, blank=True)
#     quartier = models.TextField(null=True, blank=True)
#     telephone = models.CharField(max_length=50, null=True, blank=True)
#     email = models.EmailField(null=True, blank=True)
    

     
#     # 🔹 NOUVEAU : Lien avec l'utilisateur RH qui a créé l'employé
#     # 🔹 AJOUTEZ CE CHAMP
#     created_by = models.ForeignKey(
#         settings.AUTH_USER_MODEL, 
#         on_delete=models.CASCADE,
#         related_name='employes_crees',
#         null=True,  # Temporaire pour la migration
#         blank=True
#     )

#     # 🔹 Photo de l'employé
#     photo = models.ImageField(
#         upload_to='photos_employes/',
#         null=True,
#         blank=True,
#         validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
#     )

#     # 🔹 Paramètres pour suivre la photo
#     photo_taille = models.PositiveIntegerField(null=True, blank=True, help_text="Taille du fichier en octets")
#     photo_type = models.CharField(max_length=10, null=True, blank=True, help_text="Extension du fichier")
#     photo_largeur = models.PositiveIntegerField(null=True, blank=True, help_text="Largeur en pixels")
#     photo_hauteur = models.PositiveIntegerField(null=True, blank=True, help_text="Hauteur en pixels")
#     photo_validee = models.BooleanField(default=False, help_text="Statut de validation de la photo")

#     def __str__(self):
#         return f"{self.numero_matricule} - {self.nom} {self.prenoms}"
    
#     @property
#     def age(self):
#         """Calcule l'âge automatiquement à partir de la date de naissance"""
#         if self.date_naissance:
#             today = date.today()
#             age = today.year - self.date_naissance.year - (
#                 (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day)
#             )
#             return age
#         return None
    
#     @property
#     def retraite(self):
#         """Détermine si l'employé est à la retraite (≥ 60 ans)"""
#         age = self.age
#         if age is not None:
#             return "Oui" if age >= 60 else "Non"
#         return "Non spécifié"
    
#     def save(self, *args, **kwargs):
#         if self.photo:
#             self.photo_taille = self.photo.size
#             self.photo_type = self.photo.name.split('.')[-1].lower()
#             from PIL import Image
#             img = Image.open(self.photo)
#             self.photo_largeur, self.photo_hauteur = img.size
#         super().save(*args, **kwargs)



class InformationPersonnelle(TimeStampModel):
    
    SEXE_CHOICES = [
        ('Masculin', 'Masculin'),
        ('Féminin', 'Féminin'),
    ]

    SECTION_CHOICES = [
        ('ADMINISTRATION', 'ADMINISTRATION'),
        ('BRODERIE MACHINE', 'BRODERIE MACHINE'),
        ('BRODERIE MAIN AK17', 'BRODERIE MAIN AK17'),
        ('BRODERIE MAIN DEV', 'BRODERIE MAIN DEV'),
        ('BUREAU DE METHODE', 'BUREAU DE METHODE'),
        ('CONTROLE QUALITE AS', 'CONTROLE QUALITE AS'),
        ('CHAINE 1', 'CHAINE 1'),
        ('CHAINE 2', 'CHAINE 2'),
        ('CHAINE 3', 'CHAINE 3'),
        ('CHAINE 4', 'CHAINE 4'),
        ('CHAINE 5', 'CHAINE 5'),
        ('CHAINE 6', 'CHAINE 6'),
        ('CHAINE 7', 'CHAINE 7'),
        ('CHAINE 8', 'CHAINE 8'),
        ('CHAINE 9', 'CHAINE 9'),
        ('CHAINE 10', 'CHAINE 10'),
        ('CHAINE 11', 'CHAINE 11'),
        ('CHAINE 12', 'CHAINE 12'),
        ('CHAINE CUIR', 'CHAINE CUIR'),
        ('COLLECTION', 'COLLECTION'),
        ('COUPE', 'COUPE'),
        ('COUPE COLLECTION', 'COUPE COLLECTION'),
        ('FINITION D', 'FINITION D'),
        ('FINITION M', 'FINITION M'),
        ('FINITION P', 'FINITION P'),
        ('FINITION Q', 'FINITION Q'),
        ('FINITION R', 'FINITION R'),
        ('LECTRA', 'LECTRA'),
        ('LEMARIE HVA', 'LEMARIE HVA'),
        ('MAINTENANCE', 'MAINTENANCE'),
        ('MAISON', 'MAISON'),
        ('PACKING/EXPEDITION', 'PACKING/EXPEDITION'),
        ('PLISSE', 'PLISSE'),
        ('POLE QUALITE 1', 'POLE QUALITE 1'),
        ('POLE QUALITE 2', 'POLE QUALITE 2'),
        ('RAPHIA 1', 'RAPHIA 1'),
        ('RAPHIA 2', 'RAPHIA 2'),
        ('RAPHIA 3', 'RAPHIA 3'),
        ('RAPHIA 4', 'RAPHIA 4'),
        ('RAPHIA 5', 'RAPHIA 5'),
        ('RAPHIA 6', 'RAPHIA 6'),
        ('RESPONSABLE 0', 'RESPONSABLE 0'),
        ('RESPONSABLE 1', 'RESPONSABLE 1'),
        ('RESPONSABLE 2', 'RESPONSABLE 2'),
        ('RESPONSABLE 3', 'RESPONSABLE 3'),
        ('RESPONSABLE RAPHIA', 'RESPONSABLE RAPHIA'),
        ('SECURITE', 'SECURITE'),
    ]

    numero_matricule = models.CharField(max_length=50, unique=True)
    nom = models.CharField(max_length=100)
    prenoms = models.CharField(max_length=100)
    sexe = models.CharField(max_length=10, choices=SEXE_CHOICES, null=True, blank=True)
    appellation = models.CharField(max_length=100, null=True, blank=True)
    section = models.CharField(
        max_length=50, 
        choices=SECTION_CHOICES, 
        null=True, 
        blank=True,
        help_text="Section de l'employé"
    )
    fonction = models.CharField(max_length=100, null=True, blank=True)
    date_naissance = models.DateField(null=True, blank=True)
    lieu_naissance = models.CharField(max_length=100, null=True, blank=True)
    CIN = models.CharField(max_length=50, null=True, blank=True)
    date_CIN = models.DateField(null=True, blank=True)
    lieu_CIN = models.CharField(max_length=100, null=True, blank=True)
    numero_cnaps = models.CharField(max_length=50, null=True, blank=True)
    ancien_numero_journaliere = models.CharField(max_length=50, null=True, blank=True)
    pere = models.CharField(max_length=100, null=True, blank=True)
    mere = models.CharField(max_length=100, null=True, blank=True)
    adresse = models.TextField(null=True, blank=True)
    quartier = models.TextField(null=True, blank=True)
    telephone = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    
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
        return f"{self.numero_matricule} - {self.nom} {self.prenoms}"
    
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
    
    def save(self, *args, **kwargs):
        if self.photo:
            self.photo_taille = self.photo.size
            self.photo_type = self.photo.name.split('.')[-1].lower()
            from PIL import Image
            img = Image.open(self.photo)
            self.photo_largeur, self.photo_hauteur = img.size
        super().save(*args, **kwargs)


#class vaovao start
class DossierPersonnel(TimeStampModel):
    employe = models.OneToOneField(InformationPersonnelle, on_delete=models.CASCADE, related_name='dossier_personnel')

    cv = models.FileField(
        upload_to='dossiers/cv/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    lettre_motivation = models.FileField(
        upload_to='dossiers/lettres/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    residence = models.FileField(
        upload_to='dossiers/residences/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    cin = models.FileField(
        upload_to='dossiers/cin/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    carte_cnaps = models.FileField(
        upload_to='dossiers/cnaps/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    rib = models.FileField(
        upload_to='dossiers/rib/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    photo_identite = models.FileField(
        upload_to='dossiers/photos/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    certificat_travail = models.FileField(
        upload_to='dossiers/certificats/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )

    def __str__(self):
        return f"Dossier de {self.employe.nom} {self.employe.prenoms}"
#class vaovao end




class InformationBancaire(TimeStampModel):
    employe = models.OneToOneField(InformationPersonnelle, on_delete=models.CASCADE, related_name='bancaire')
    nom_banque = models.CharField(max_length=100, null=True, blank=True)
    cle_rib = models.CharField(max_length=10, null=True, blank=True)


class InformationSociale(TimeStampModel):
    employe = models.OneToOneField(InformationPersonnelle, on_delete=models.CASCADE, related_name='sociale')
    retraite = models.CharField(max_length=50, null=True, blank=True)
    enfant_allocation = models.IntegerField(default=0, null=True, blank=True)


class InformationFamiliale(TimeStampModel):
    employe = models.OneToOneField(InformationPersonnelle, on_delete=models.CASCADE, related_name='familiale')

    # Informations sur l'époux(se)
    epoux_nom = models.CharField(max_length=100, null=True, blank=True)
    epoux_prenoms = models.CharField(max_length=100, null=True, blank=True)
    epoux_date_naissance = models.DateField(null=True, blank=True)
    epoux_lieu_naissance = models.CharField(max_length=100, null=True, blank=True)
    epoux_societe = models.CharField(max_length=150, null=True, blank=True)
    epoux_fonction = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Famille de {self.employe.nom} {self.employe.prenoms}"




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

# class InformationSalairePersonnel(TimeStampModel):
#     employe = models.OneToOneField('InformationPersonnelle', on_delete=models.CASCADE, related_name='salaire_personnel')
#     date_embauche = models.DateField(null=True, blank=True)
#     responsable_section = models.CharField(max_length=100, null=True, blank=True)
#     categorie = models.CharField(max_length=50, null=True, blank=True)
#     indice = models.CharField(max_length=20, null=True, blank=True, help_text="Indice de l'employé")
#     taux_horaire = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Taux horaire en Ariary")
#     salaire_base = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Salaire de base en Ariary")
#     autre_indemnite = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Autres indemnités en Ariary")
#     prime_anciennete = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
#     indemnite_deplacement = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
#     dernier_aug_indice = models.CharField(max_length=50, null=True, blank=True)
#     salaire_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Salaire total calculé en Ariary")

#     def __str__(self):
#         return f"Salaire de {self.employe.nom_prenoms} - {self.fonction}"


class InformationSalairePersonnel(TimeStampModel):
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

    employe = models.OneToOneField('InformationPersonnelle', on_delete=models.CASCADE, related_name='salaire_personnel')
    date_embauche = models.DateField(null=True, blank=True)
    responsable_section = models.CharField(max_length=100, null=True, blank=True)
    categorie = models.CharField(
        max_length=10, 
        choices=CATEGORIE_CHOICES, 
        null=True, 
        blank=True,
        help_text="Catégorie de l'employé"
    )
    indice = models.CharField(max_length=20, null=True, blank=True, help_text="Indice de l'employé")
    taux_horaire = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Taux horaire en Ariary")
    salaire_base = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Salaire de base en Ariary")
    autre_indemnite = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Autres indemnités en Ariary")
    prime_anciennete = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    indemnite_deplacement = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    dernier_aug_indice = models.CharField(max_length=50, null=True, blank=True)
    salaire_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Salaire total calculé en Ariary")

    def __str__(self):
        return f"Salaire de {self.employe.nom} {self.employe.prenoms}"
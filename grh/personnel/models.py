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

class TimeStampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class InformationPersonnelle(TimeStampModel):
    SEXE_CHOICES = [
        ('Masculin', 'Masculin'),
        ('Féminin', 'Féminin'),
    ]

    numero_matricule = models.CharField(max_length=50, unique=True)
    nom = models.CharField(max_length=100)
    prenoms = models.CharField(max_length=100)
    sexe = models.CharField(max_length=10, choices=SEXE_CHOICES, null=True, blank=True)
    appellation = models.CharField(max_length=100, null=True, blank=True)
    section = models.CharField(max_length=100, null=True, blank=True)
    fonction = models.CharField(max_length=100, null=True, blank=True)
    date_naissance = models.DateField(null=True, blank=True)
    lieu_naissance = models.CharField(max_length=100, null=True, blank=True)
    CIN = models.CharField(max_length=50, null=True, blank=True)
    date_CIN = models.DateField(null=True, blank=True)
    lieu_CIN=models.CharField(max_length=100, null=True, blank=True)
    numero_cnaps = models.CharField(max_length=50, null=True, blank=True)
    ancien_numero_journaliere = models.CharField(max_length=50, null=True, blank=True)
    pere = models.CharField(max_length=100, null=True, blank=True)
    mere = models.CharField(max_length=100, null=True, blank=True)
    adresse = models.TextField(null=True, blank=True)
    quartier = models.TextField(null=True, blank=True)
    telephone = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    #mobile_money = models.CharField(max_length=50, null=True, blank=True)
    #photo = models.ImageField(upload_to='photos/', null=True, blank=True)
    #photo_1 = models.ImageField(upload_to='photos/', null=True, blank=True)

    def __str__(self):
        return f"{self.numero_matricule} - {self.nom} {self.prenoms}"
    
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


# class InformationProfessionnelle(TimeStampModel):
#     employe = models.OneToOneField(InformationPersonnelle, on_delete=models.CASCADE, related_name='professionnelle')
#     #fonction = models.CharField(max_length=100, null=True, blank=True)
#     #section = models.CharField(max_length=100, null=True, blank=True)
#     #appellation = models.CharField(max_length=100, null=True, blank=True)
#     date_embauche = models.DateField(null=True, blank=True)
#     date_debauche = models.DateField(null=True, blank=True)
#     #ancien_numero = models.CharField(max_length=50, null=True, blank=True)
#     titre_poste = models.CharField(max_length=100, null=True, blank=True)
#     departement = models.CharField(max_length=100, null=True, blank=True)
#     secteur = models.CharField(max_length=100, null=True, blank=True)
#     code_fonction = models.CharField(max_length=50, null=True, blank=True)
#     section_temporaire = models.CharField(max_length=100, null=True, blank=True)
#     pour_responsable = models.CharField(max_length=100, null=True, blank=True)
#     depart = models.CharField(max_length=100, null=True, blank=True)
#     motif_depart = models.TextField(null=True, blank=True)


class InformationBancaire(TimeStampModel):
    employe = models.OneToOneField(InformationPersonnelle, on_delete=models.CASCADE, related_name='bancaire')
    nom_banque = models.CharField(max_length=100, null=True, blank=True)
    code_banque = models.CharField(max_length=50, null=True, blank=True)
    code_agence = models.CharField(max_length=50, null=True, blank=True)
    numero_compte = models.CharField(max_length=50, null=True, blank=True)
    cle_rib = models.CharField(max_length=10, null=True, blank=True)
    banque_beneficiaire = models.CharField(max_length=100, null=True, blank=True)


class InformationSociale(TimeStampModel):
    employe = models.OneToOneField(InformationPersonnelle, on_delete=models.CASCADE, related_name='sociale')
    #numero_cnaps = models.CharField(max_length=50, null=True, blank=True)
    retraite = models.CharField(max_length=50, null=True, blank=True)
    enfant_allocation = models.IntegerField(default=0, null=True, blank=True)

# 🔹 Nouvelle classe : Information Familiale
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


# 🔹 Informations sur les enfants
class Enfant(TimeStampModel):
    familiale = models.ForeignKey(InformationFamiliale, on_delete=models.CASCADE, related_name='enfants')
    nom_prenoms = models.CharField(max_length=150)
    sexe = models.CharField(max_length=10, choices=[('Masculin', 'Masculin'), ('Féminin', 'Féminin')])
    date_naissance = models.DateField(null=True, blank=True)
    lieu_naissance = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.nom_prenoms} ({self.sexe})"



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


class InformationSalairePersonnel(TimeStampModel):
    employe = models.OneToOneField('InformationPersonnelle', on_delete=models.CASCADE, related_name='salaire_personnel')
    date_embauche = models.DateField(null=True, blank=True)
    fonction = models.CharField(max_length=100, null=True, blank=True)
    categorie = models.CharField(max_length=50, null=True, blank=True)
    salaire = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    section = models.CharField(max_length=100, null=True, blank=True)
    responsable_section = models.CharField(max_length=100, null=True, blank=True)
    prime_anciennete = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    indemnite_deplacement = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    dernier_aug_indice = models.CharField(max_length=50, null=True, blank=True)
    pour_30 = models.CharField(max_length=50, null=True, blank=True)
    T1_17 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    T2_17 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    T3_17 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    T4_17 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    obs_prime = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Salaire de {self.employe.nom_prenoms} - {self.fonction}"

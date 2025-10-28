from django.db import models
from django.utils import timezone

# Model de base pour timestamp (création / mise à jour)
class TimeStampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

# Model Employé (table principale)
class Employe(TimeStampModel):
    matricule = models.CharField(max_length=20, unique=True)
    nom = models.CharField(max_length=50)
    prenoms = models.CharField(max_length=100)
    fonction = models.CharField(max_length=100)
    section = models.CharField(max_length=100)
    appelation = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.matricule} - {self.nom} {self.prenoms}"

# Informations sur le poste
class Poste(TimeStampModel):
    employe = models.OneToOneField(Employe, on_delete=models.CASCADE, related_name='poste')
    titre_poste = models.CharField(max_length=100)
    date_embauche = models.DateField()
    type_contrat = models.CharField(max_length=50, choices=[('CDD','CDD'), ('CDI','CDI')])
    salaire = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

# Informations bancaires
class Banque(TimeStampModel):
    employe = models.OneToOneField(Employe, on_delete=models.CASCADE, related_name='banque')
    nom_banque = models.CharField(max_length=100)
    numero_compte = models.CharField(max_length=50)
    iban = models.CharField(max_length=34, blank=True, null=True)

# Informations sociales
class Social(TimeStampModel):
    employe = models.OneToOneField(Employe, on_delete=models.CASCADE, related_name='social')
    num_cnaps = models.CharField(max_length=50, blank=True, null=True)
    num_ostie = models.CharField(max_length=50, blank=True, null=True)
    assurance_sante = models.CharField(max_length=100, blank=True, null=True)

# Pièces d'identité
class Identite(TimeStampModel):
    employe = models.OneToOneField(Employe, on_delete=models.CASCADE, related_name='identite')
    num_carte_identite = models.CharField(max_length=50)
    date_naissance = models.DateField()
    lieu_naissance = models.CharField(max_length=100)
    adresse = models.TextField()

# Documents de l'employé (plusieurs fichiers possibles)
class Document(TimeStampModel):
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='documents')
    type_document = models.CharField(max_length=50, choices=[
        ('CV', 'CV'), 
        ('Contrat', 'Contrat'), 
        ('Lettre', 'Lettre de motivation'), 
        ('Autre', 'Autre')
    ])
    fichier = models.FileField(upload_to='documents_employes/')
    date_ajout = models.DateTimeField(default=timezone.now)

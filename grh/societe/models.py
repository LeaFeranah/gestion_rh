from django.db import models
from django.utils import timezone
from treebeard.mp_tree import MP_Node

#from rest_framework.decorators import action
class TimeStampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True

    def delete(self):
        #self.deleted_at = django.utils.timezone.now()
        self.deleted_at = timezone.now()
        self.save()

    def hard_delete(self):
        super(SoftDeletionModel, self).delete()

class InfoSociete(TimeStampModel):
    name = models.CharField(max_length=100, blank=True, null=True)
    adresse = models.CharField(max_length=255, blank=True, null=True)
    raison_social = models.CharField(max_length=255, blank=True, null=True)
    rcs = models.CharField(max_length=20, blank=True, null=True)
    nif = models.CharField(max_length=20, blank=True, null=True)
    stat = models.CharField(max_length=20, blank=True, null=True)
    ostie = models.CharField(max_length=20, blank=True, null=True)
    cnaps = models.CharField(max_length=20, blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

    #class Meta:
        #db_table = 'societe'
"""
    @action(detail=False, methods=['GET'])
    def list(self):
        return 'boooo'
"""
class Departement(TimeStampModel):
    name = models.CharField(max_length=100, blank=True, null=True)
    societe =  models.ForeignKey(InfoSociete, on_delete = models.CASCADE)

    def __str__(self):
        return self.name


class Service(TimeStampModel):
    name = models.CharField(max_length=100, blank=True, null=True)
    departement=models.ForeignKey(Departement, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Section(TimeStampModel):
    name = models.CharField(max_length=100, blank=True, null=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Fonction(TimeStampModel):
    name = models.CharField(max_length=100, blank=True, null=True)
    niveau = models.SmallIntegerField(blank=True, null=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Horaire(TimeStampModel):
    heure_entree = models.DateTimeField(blank=True, null=True)
    heure_sortie = models.DateTimeField(blank=True, null=True)
    duree_pause = models.FloatField(blank=True, null=True)
    fonction = models.ForeignKey(Fonction, on_delete=models.CASCADE)

class JourFerie(TimeStampModel):
    annee = models.IntegerField(blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    jour = models.CharField(max_length=10, blank=True, null=True)
    name = models.CharField(max_length=50, blank=True, null=True)
    est_deductible = models.BooleanField(null=True)

    def __str__(self):
        return self.name
'''
class Hierarchie(TimeStampModel):
    nom_poste = models.CharField(max_length=100, null=True)
    superieur = models.IntegerField()
    niveau = models.IntegerField()
    #societe_id = models.IntegerField(default=0)
    societe = models.ForeignKey(InfoSociete, on_delete=models.CASCADE)

    def __str__(self):
        return self.nom_poste
'''

class Hierarchie(MP_Node):
    nom_poste = models.CharField(max_length=100, null=True)
    node_order_by = ['nom_post']
    def __str__(self):
        return f'Poste :{self.nom_poste}'

class Organe(TimeStampModel):
    nom_organe = models.CharField(max_length=100, null=True)
    societe = models.ForeignKey(InfoSociete, on_delete=models.CASCADE)
    hierarchie = models.ForeignKey(Hierarchie, on_delete=models.CASCADE)

from django.shortcuts import render
from rest_framework import viewsets
# Create your views here.
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import DepartementSerializer,SectionSerializer,ServiceSerializer, SocieteSerializer,SectionSerializer, HierarchieSerializer,OrganeSerializer
from rest_framework.response import Response
from .models import Departement, Service, InfoSociete as Societe, Section, Hierarchie, Organe
#from rest_framework import authentication, permissions
#from django.contrib.auth.models import User

from rest_framework.decorators import action
from rest_framework import status

class DepartementViewSet(viewsets.ModelViewSet):
    queryset = Departement.objects.all()
    serializer_class = DepartementSerializer

    def list (self, request, societe_id):
        departement = Departement.objects.all().filter(societe_id = societe_id).exclude(deleted_at__isnull = False)
        serializer = DepartementSerializer(departement, many = True)
        return Response(serializer.data)

    def create (self, request, *args, **kwargs):
        #print(f'===> request : {request.data}')
        serializer = DepartementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status = status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        departement = self.get_object()
        serializer = DepartementSerializer(departement, data = request.data, partial = True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status = status.HTTP_200_OK)
        else:
            return Response(serializer.error, status = status.HTTP_400_BAD_REQUEST)

    def destroy(self , request, pk=None):
        #print(f'===> primary key = {pk}')
        try:
            departement = Departement.objects.get(pk=pk)
            print(f'===> departement to delete : {departement}')
            if departement:
                #Remove Services
                services = Service.objects.all().filter(departement_id = pk).exclude(deleted_at__isnull = False)
                print(f'services ==> {services}')
                for service in services:
                    service.delete()

                departement.delete()
                return Response({'success':'Delete Success'}, status = status.HTTP_200_OK)
            else:
                return Response({'faild':'Operation Faild'}, status = status.HTTP_406_NOT_ACCEPTABLE)
        except:
            return Response({'message':'Departement not available'})

    """
        serializer = DepartementSerializer(queryset, many = True)
        return Response(serializer.data)
    def retrieve(self, request, pk = None):
        queryset = Departement.objects.all()
        dep = get_object_or_404(queryset, pk = pk)
        serializer = DepartementSerializer(dep)
        return Response(serializer.data)
    """
class SocieteViewSet(viewsets.ModelViewSet):
    queryset = Societe.objects.all()
    serializer_class = SocieteSerializer

    #@action(detail = False )
    def liste(self, request):
        societe = Societe.objects.all().exclude(deleted_at__isnull = False)
        serializer = SocieteSerializer(societe, many = True)
        return Response(serializer.data)

    def partial_update(self, request, pk=None):

        societe = self.get_object()
        serializer = SocieteSerializer(societe, data = request.data, partial = True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status = status.HTTP_200_OK)

        else:
            return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk):
        try:
            societe = Societe.objects.get(pk=pk)
        except Societe.DoesNotExist:
            return Response({'message':'Societe not available'})

        serializer = SocieteSerializer(societe);
        return Response(serializer.data)

    def destroy(self, request, pk):
        try:
            societe = Societe.objects.get(pk=pk)
            if societe:
                #Select departement
                departements = Departement.objects.all().filter(societe_id = pk).exclude(deleted_at__isnull = False)
                for departement in departements:
                    #print(departement)
                    departement.delete()

                societe.delete()
                societes = Societe.objects.all().exclude(deleted_at__isnull = False)
                serializer = SocieteSerializer(societes, many = True)
                return Response(serializer.data)

            else:
                return Response({'failed':'Operation failed'}, status = status.HTTP_406_NOT_ACCEPTABLE)
        except Societe.DoesNotExist:
            print('delete :except')
            return Response({'message':'Societe not available'})

class ServiceViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceSerializer
    queryset = Service.objects.all()

    def list(self, request, departement_id):
        #print(f'===> departement id : {departement_id}')
        services = Service.objects.all().filter(departement_id = departement_id).exclude(deleted_at__isnull = False)
        serializer = ServiceSerializer(services, many = True)
        return Response(serializer.data, status = status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = ServiceSerializer(data=request.data)
        if serializer.is_valid(raise_exception = True):
            serializer.save()
            return Response(status = status.HTTP_201_CREATED)

        #if serializer.is_valid():
        else:
            return Response(serializer.error, status = status.HTTP_406_NOT_ACCEPTABLE)

    def partial_update(self, request, pk=None):
        service = self.get_object()
        serializer = ServiceSerializer(service, data = request.data, partial = True)
        if serializer.is_valid():
            serializer.save()
            return Response(status = status.HTTP_200_OK)
        else:
            return Response(serializer.error, status = status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk):
        try:
            service = Service.objects.get(pk=pk)
            #print(f' ===> pk to delete : {pk}')
            #service = Service.objects.all().filter().exclude(deleted_at__isnull = False)
            service.delete()
            return Response({'success':'Delete Success'}, status = status.HTTP_200_OK)
        except:
            return Response({'message':'Service not available'})

class SectionViewSet(viewsets.ModelViewSet):
    serializer_class = SectionSerializer
    queryset = Section.objects.all()

    def list(self, request, service_id):
        sections = Section.objects.all().filter(service_id = service_id).exclude(deleted_at__isnull = False)
        serializer = SectionSerializer(sections, many = True)
        return Response(serializer.data, status = status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = SectionSerializer(data = request.data)
        if serializer.is_valid(raise_exception = True):
            serializer.save()
            return Response(status = status.HTTP_201_CREATED)
        else:
            return Response(serializer.error, status = status.HTTP_406_NOT_ACCEPTABLE)

    def partial_update(self, request, pk=None):
        section = self.get_object()
        serializer = SectionSerializer(section, data = request.data, partial = True)
        if serializer.is_valid():
            serializer.save()
            return Response(status = status.HTTP_200_OK)
        else:
            return Response(serializer.error, status = status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk):
        try:
            section = Section.objects.get(pk = pk)
            section.delete()
            return Response({'success':'Delete Success'}, status = status.HTTP_200_OK)
        except:
            return Response({'message':'Section not available'})

class OrganeViewSet(viewsets.ModelViewSet):
    serializer_class = OrganeSerializer
    queryset = Organe.objects.all()

    def list(self, resquest, societe_id):
        lists = Organe.objects.all().filter(societe_id = societe_id).exclude(deleted_at__isnull = False)
        serializer = OrganeSerializer(lists, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = OrganeSerializer(data=request.data)
        #request.data['societe_id'] = 3
        root = Hierarchie.add_root(nom_poste = request.data['nom_poste'])
        request.data['hierarchie']=root.pk
        print(request.data)

        if serializer.is_valid():
            serializer.save;
            return Response(status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_406_NOT_ACCEPTABLE)

class HierarchieViewSet(viewsets.ModelViewSet):
    serializer_class = HierarchieSerializer
    queryseet = Hierarchie.objects.all()

"""
class HierarchieViewSet(viewsets.ModelViewSet):
    serializer_class = HierarchieSerializer
    queryset = Hierarchie.objects.all()

    def list(self, request, societe_id):
        lists = Hierarchie.objects.all().filter(societe_id = societe_id).exclude(deleted_at__isnull = False)
        serializer = HierarchieSerializer(lists, many = True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def list_base(self, request, societe_id):
        lists = Hierarchie.objects.all().filter(societe_id = societe_id, superieur = 0, niveau = 0).exclude(deleted_at__isnull = False)
        serializer = HierarchieSerializer(lists, many = True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = HierarchieSerializer(data = request.data)
        if serializer.is_valid():
            serializer.save();
            return Response(status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.error, status=status.HTTP_406_NOT_ACCEPTABLE)

    def partial_update(self, request, pk=None):
        hierarchie = self.get_object()
        serializer = HierarchieSerializer(hierarchie, data = request.data, partial = True)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk):
        try:
            #hierarchie = Hierarchie.objects.get(pk=pk)
            hierarchie = self.get_object()
            hierarchie.delete()
            return Response(status=status.HTTP_200_OK)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)
"""
"""
class Societe(viewsets.ModelViewSet):
    serializer_class = SocieteSerializer
    queryset = Societe.objects.all()

    def retrieve(self,  )
class Departement(viewsets.ModelViewSet):

    serializer_class = DepartementSerializer
    queryset = Departement.objects.all()



class SocieteViewSet(viewsets.ViewSet):

    #queryset = Societe.objects.all()

    def list(self, request):
        queryset = Societe.objects.all()
        serializer =  SocieteSerializer(queryset, many = True)
        return Response(serializer.data)

        print(request)
        return Response(serializer.data)


"""

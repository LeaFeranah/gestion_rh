#from rest_framework import routers
from django.urls import path, include
from .views import SocieteViewSet, DepartementViewSet, ServiceViewSet, SectionViewSet, HierarchieViewSet, OrganeViewSet
from rest_framework import renderers

#router = routers.DefaultRouter()
#router = routers.SimpleRouter()
#router.register('departement', viewset = views.Departement)
#router.register('service', viewset = views.Service)
#router.register('societe', SocieteViewSet, basename = 'Societe')
#router.register('societe', SocieteViewSet)

societe_liste = SocieteViewSet.as_view({
    'get':'liste'
})#,renderer_classes = [renderers.StaticHTMLRenderer])

societe_patchSociete = SocieteViewSet.as_view({
    'patch':'patchSociete'
})

societe_list = SocieteViewSet.as_view({
    'get':'list',
    'post':'create'
})

societe_detail = SocieteViewSet.as_view({
    'get':'retrieve',
    'put':'update',
    'patch':'partial_update',
    'delete':'destroy'
})

departements = DepartementViewSet.as_view({
    'get':'list',
    'post':'create',
})

departement = DepartementViewSet.as_view({
    'patch':'partial_update',
    'delete':'destroy'
})

services = ServiceViewSet.as_view({
    'get':'list',
    'post':'create'
})

service = ServiceViewSet.as_view({
    'patch':'partial_update',
    'delete':'destroy'
})

sections = SectionViewSet.as_view({
    'get':'list',
    'post':'create'
})

section = SectionViewSet.as_view({
    'patch':'partial_update',
    'delete':'destroy'
})

hierarchies = HierarchieViewSet.as_view({
    'get':'list',
    'post':'create'
})

hierarchie = HierarchieViewSet.as_view({
    'patch':'partial_update',
    'delete':'destroy'
})

hierarchies_base = HierarchieViewSet.as_view({
    'get':'list_base'
})

organes = OrganeViewSet.as_view({
    'get':'list',
    'post':'create'
})

urlpatterns = [
    path('societe/liste/', societe_liste, name = "societe-liste-test"),
    path('societe/', societe_list, name = 'societe'),
    path('societe/<int:pk>', societe_detail, name ='societe-detail'),

    path('departements/<int:societe_id>', departements, name ='departements'),
    path('departement/<int:pk>', departement, name = 'departement'),

    path('services/<int:departement_id>', services, name = 'services'),
    path('service/<int:pk>', service, name = 'service'),

    path('sections/<int:service_id>', sections, name = 'sections'),
    path('section/<int:pk>', section, name = 'section'),

    path('hierarchies/<int:societe_id>', hierarchies, name = 'hierarchies'),
    path('hierarchies/base/<int:societe_id>', hierarchies_base, name = 'hierarchies_base'),
    path('hierarchie/<int:pk>', hierarchie, name = 'hierarchie'),

    path('organes/<int:societe_id>', organes, name='organes')

]



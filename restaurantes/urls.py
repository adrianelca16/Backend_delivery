# restaurantes/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RestauranteViewSet, EstadoRestauranteViewSet, PlatoViewSet, CategoriasRestauranteViewSet, TipoOpcionViewSet, OpcionPlatoViewSet

router = DefaultRouter()
router.register('restaurantes', RestauranteViewSet, basename='restaurante')
router.register('estados', EstadoRestauranteViewSet)
router.register('categorias', CategoriasRestauranteViewSet)
router.register('platos', PlatoViewSet)
router.register('tipos-opciones', TipoOpcionViewSet, basename='tipos-opciones' )
router.register('opciones', OpcionPlatoViewSet, basename='opciones')

urlpatterns = [
    path('', include(router.urls)),
]

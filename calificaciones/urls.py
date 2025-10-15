# calificaciones/urls.py
from rest_framework.routers import DefaultRouter
from .views import CalificacionViewSet

router = DefaultRouter()
router.register(r'calificaciones', CalificacionViewSet, basename='calificacion')

urlpatterns = router.urls

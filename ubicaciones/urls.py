from rest_framework.routers import DefaultRouter
from .views import UbicacionConductorViewSet

router = DefaultRouter()
router.register(r'ubicaciones', UbicacionConductorViewSet, basename='ubicacion')

urlpatterns = router.urls

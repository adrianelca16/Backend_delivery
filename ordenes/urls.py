from rest_framework.routers import DefaultRouter
from .views import EstadoOrdenViewSet, OrdenViewSet

router = DefaultRouter()
router.register(r'estados-orden', EstadoOrdenViewSet)
router.register(r'ordenes', OrdenViewSet)

urlpatterns = router.urls

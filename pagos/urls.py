from rest_framework.routers import DefaultRouter
from .views import MetodoPagoViewSet, PagoViewSet

router = DefaultRouter()
router.register(r'metodos-pago', MetodoPagoViewSet, basename='metodopago')
router.register(r'pagos', PagoViewSet, basename='pago')

urlpatterns = router.urls

from rest_framework.routers import DefaultRouter
from .views import WalletViewSet, MovimientoViewSet

router = DefaultRouter()
router.register(r'wallets', WalletViewSet, basename='wallet')
router.register(r'movimientos', MovimientoViewSet, basename='movimiento')

urlpatterns = router.urls

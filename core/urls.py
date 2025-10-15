from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterView, LoginView, RolViewSet, DireccionViewSet, UsuarioViewSet, ConductorViewSet

router = DefaultRouter()
router.register(r'roles', RolViewSet, basename='rol')
router.register(r'direcciones', DireccionViewSet, basename='direccion')
router.register(r'usuario', UsuarioViewSet, basename='usuario')
router.register(r'conductor', ConductorViewSet, basename='conductor')

urlpatterns = [
    path('register/', RegisterView.as_view(), name="register"),
    path('login/', LoginView.as_view(), name="login"),
    path('', include(router.urls)),  # 👉 esto mete todas las rutas del router
]

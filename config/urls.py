from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/user/', include('core.urls')),
    path('api/restaurantes/', include('restaurantes.urls')),
    path('api/ubicaciones/', include('ubicaciones.urls')),
    path('api/ordenes/', include('ordenes.urls')),
    path('api/auditoria/', include('auditoria.urls')),
    path('api/calificaciones/', include('calificaciones.urls')),
    path('api/notificaciones/', include('notificaciones.urls')),
    path('api/pagos/', include('pagos.urls')),
    path('api/wallet/', include('wallet.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
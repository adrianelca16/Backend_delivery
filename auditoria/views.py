from django.shortcuts import render

# Create your views here.
# auditoria/views.py
from rest_framework import viewsets, permissions
from .models import Auditoria
from .serializers import AuditoriaSerializer
from core.permissions import IsAdmin

class AuditoriaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Auditoria.objects.all().order_by('-fecha')
    serializer_class = AuditoriaSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

# calificaciones/serializers.py
from rest_framework import serializers
from .models import Calificacion

class CalificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Calificacion
        fields = '__all__'
        read_only_fields = ['cliente', 'creado_en']

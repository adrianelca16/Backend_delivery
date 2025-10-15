from rest_framework import serializers
from .models import UbicacionConductor

class UbicacionConductorSerializer(serializers.ModelSerializer):
    class Meta:
        model = UbicacionConductor
        fields = ['id', 'conductor', 'latitud', 'longitud', 'actualizado_en']
        read_only_fields = ['actualizado_en', 'conductor']

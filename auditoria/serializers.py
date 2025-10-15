# auditoria/serializers.py
from rest_framework import serializers
from .models import Auditoria

class AuditoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Auditoria
        fields = '__all__'
        read_only_fields = ['usuario', 'fecha']

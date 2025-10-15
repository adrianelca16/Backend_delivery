# restaurantes/permissions.py

from rest_framework.permissions import BasePermission

class IsComercio(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol.nombre == 'comercio'


class IsCliente(BasePermission):
    def has_permission(self, request, view):
        return request.user.rol.nombre == 'cliente'

class IsConductor(BasePermission):
    def has_permission(self, request, view):
        return request.user.rol.nombre == 'conductor'

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.rol.nombre == 'admin'

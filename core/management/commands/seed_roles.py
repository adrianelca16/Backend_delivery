from django.core.management.base import BaseCommand
from core.models import Rol, EstadoUsuario
from restaurantes.models import CategoriaRestaurante, EstadoRestaurante
from pagos.models import MetodoPago
from ordenes.models import EstadoOrden

class Command(BaseCommand):
    help = 'Crea los roles base del sistema'

    def handle(self, *args, **kwargs):
        roles = ['admin', 'cliente', 'conductor', 'comercio']
        for nombre in roles:
            rol, creado = Rol.objects.get_or_create(nombre=nombre)
            if creado:
                self.stdout.write(self.style.SUCCESS(f'Rol "{nombre}" creado.'))
            else:
                self.stdout.write(self.style.WARNING(f'Rol "{nombre}" ya existe.'))
        
        estadoUsuario = ['activo', 'suspendido', 'anulado']
        for nombre in estadoUsuario:
            nombre, creado = EstadoUsuario.objects.get_or_create(nombre=nombre)
            if creado:
                self.stdout.write(self.style.SUCCESS(f'usuarioEstado "{nombre}" creado.'))
            else:
                self.stdout.write(self.style.WARNING(f'usuarioEstado "{nombre}" ya existe.'))
        
        categorias = ['Italiana', 'Mexicana', 'China', 'Fast Food', 'Vegana', 'Postres']
        for nombre in categorias:
            nombre, creado = CategoriaRestaurante.objects.get_or_create(nombre=nombre)
            if creado:
                self.stdout.write(self.style.SUCCESS(f'categoria "{nombre}" creado.'))
            else:
                self.stdout.write(self.style.WARNING(f'categoria "{nombre}" ya existe.'))

        metodos_pago = [
            {"nombre": "Pago movil", "icono": "send-outline", "descripcion": "Pago movil"},
            {"nombre": "Efectivo", "icono": "cash", "descripcion": "Efectivo"},
            {"nombre": "Bolívares", "icono": "wallet-outline", "descripcion": "Bolívares"},
        ]

        for metodo in metodos_pago:
            obj, creado = MetodoPago.objects.get_or_create(
                nombre=metodo["nombre"],
                defaults={
                    "icons": metodo["icono"],
                    "descripcion": metodo["descripcion"]
                }
            )
            if creado:
                self.stdout.write(self.style.SUCCESS(f'Método de pago "{obj.nombre}" creado.'))
            else:
                self.stdout.write(self.style.WARNING(f'Método de pago "{obj.nombre}" ya existe.'))

        estado_orden = [
            {"nombre": "Pago por verificar", "descripcion": "Verificación de pago en proceso (solo pago movil)"},
            {"nombre": "Pendiente", "descripcion": "Orden pendiente de aceptación por el comercio"},
            {"nombre": "Aceptada","descripcion": "Orden aceptada por el comercio"},
            {"nombre": "Asignada","descripcion": "Orden asignada a un conductor"},
            {"nombre": "En camino","descripcion": "Orden en camino hacia el cliente"},
            {"nombre": "Entregada","descripcion": "Orden entregada al cliente"},
            {"nombre": "Cancelada","descripcion": "Orden cancelada por el cliente o comercio"},
            {"nombre": "Esperando aceptacion","descripcion": "Esperando aceptacion del conductor"},
        ]

        for estado in estado_orden:
            obj, creado = EstadoOrden.objects.get_or_create(
                nombre=estado["nombre"],
                defaults={
                    "descripcion": estado["descripcion"]
                }
            )
            if creado:
                self.stdout.write(self.style.SUCCESS(f'Estado de orden "{obj.nombre}" creado.'))
            else:
                self.stdout.write(self.style.WARNING(f'Estado de orden "{obj.nombre}" ya existe.'))

        estado_restaurante = [
            {"nombre": "Activo", "descripcion": "Activo y operativo"},
            {"nombre": "Suspendido", "descripcion": "Suspendido"},
        ]

        for estado in estado_restaurante:
            obj, creado = EstadoRestaurante.objects.get_or_create(
                nombre=estado["nombre"],
                defaults={
                    "descripcion": estado["descripcion"]
                }
            )
            if creado:
                self.stdout.write(self.style.SUCCESS(f'Estado de restaurante "{obj.nombre}" creado.'))
            else:
                self.stdout.write(self.style.WARNING(f'Estado de restaurante "{obj.nombre}" ya existe.'))
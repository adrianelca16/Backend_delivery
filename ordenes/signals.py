from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from .models import Orden
from wallet.models import Wallet, Movimiento

@receiver(post_save, sender=Orden)
def crear_movimientos_wallet(sender, instance, created, **kwargs):
    """
    Cuando una orden cambia a estado 'entregada', crea los movimientos
    para el comercio, conductor y la empresa.
    """
    if not created:
        if getattr(instance, 'movimientos_generados', False):
            return

        if instance.estado.nombre.lower() == "entregada":
            subtotal = instance.subtotal or Decimal("0.00")
            comercio_monto = subtotal * Decimal("0.87")
            empresa_monto_subtotal = subtotal * Decimal("0.13")

            # Wallet comercio
            comercio_wallet = Wallet.objects.get(usuario=instance.restaurante.usuario)
            Movimiento.objects.create(
                wallet=comercio_wallet,
                tipo="ingreso",
                monto=comercio_monto,
                descripcion=f"Ingreso por orden #{instance.numero_orden} (subtotal)"
            )
            comercio_wallet.saldo += comercio_monto
            comercio_wallet.save(update_fields=["saldo"])

            # Wallet empresa
            empresa_wallet = Wallet.objects.get(usuario=instance.restaurante.empresa.usuario)
            Movimiento.objects.create(
                wallet=empresa_wallet,
                tipo="ingreso",
                monto=empresa_monto_subtotal,
                descripcion=f"Ingreso empresa por orden #{instance.numero_orden} (subtotal)"
            )
            empresa_wallet.saldo += empresa_monto_subtotal
            empresa_wallet.save(update_fields=["saldo"])

            costo_envio = instance.costo_envio or Decimal("0.00")
            if costo_envio > 0 and instance.conductor:
                primer_km = Decimal("1.00")
                if costo_envio >= primer_km:
                    conductor_primer_km = Decimal("0.75")
                    empresa_primer_km = Decimal("0.25")
                    restante_envio = costo_envio - primer_km
                else:
                    conductor_primer_km = costo_envio * Decimal("0.75")
                    empresa_primer_km = costo_envio * Decimal("0.25")
                    restante_envio = Decimal("0.00")

                if restante_envio > 0:
                    km_adicionales = restante_envio / Decimal("0.045")
                    conductor_extra = km_adicionales * Decimal("0.20")
                    empresa_extra = km_adicionales * Decimal("0.25")
                else:
                    conductor_extra = Decimal("0.00")
                    empresa_extra = Decimal("0.00")

                conductor_envio = conductor_primer_km + conductor_extra
                empresa_envio = empresa_primer_km + empresa_extra

                conductor_wallet = Wallet.objects.get(usuario=instance.conductor.usuario)
                Movimiento.objects.create(
                    wallet=conductor_wallet,
                    tipo="ingreso",
                    monto=conductor_envio,
                    descripcion=f"Pago delivery por orden #{instance.numero_orden}"
                )
                conductor_wallet.saldo += conductor_envio
                conductor_wallet.save(update_fields=["saldo"])

                Movimiento.objects.create(
                    wallet=empresa_wallet,
                    tipo="ingreso",
                    monto=empresa_envio,
                    descripcion=f"Pago empresa por envío orden #{instance.numero_orden}"
                )
                empresa_wallet.saldo += empresa_envio
                empresa_wallet.save(update_fields=["saldo"])

            instance.movimientos_generados = True
            instance.save(update_fields=["movimientos_generados"])

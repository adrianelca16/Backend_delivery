from decimal import Decimal
from django.contrib.auth import get_user_model
from wallet.models import Movimiento
from auditoria.services import registrar_auditoria

User = get_user_model()

def asignar_pago_wallet(orden):
    """
    Distribuye los pagos de una orden:
    - Restaurante: 87% del subtotal
    - Empresa (admin): 13% del subtotal + parte del envío + impuesto completo
    - Conductor: parte del envío según km
    """
    if getattr(orden, "movimientos_generados", False):
        return  # Evitar duplicar movimientos

    subtotal = orden.subtotal or Decimal("0.00")
    costo_envio = orden.costo_envio or Decimal("0.00")
    impuesto = orden.impuesto or Decimal("0.00")

    # Wallets
    restaurante_wallet = orden.restaurante.usuario.wallet
    conductor_wallet = getattr(orden.conductor, "usuario", None)
    conductor_wallet = getattr(conductor_wallet, "wallet", None)

    try:
        admin_user = User.objects.filter(is_superuser=True).first()
        empresa_wallet = admin_user.wallet
    except Exception:
        empresa_wallet = None
        admin_user = None

    # ==== SUBTOTAL ====
    restaurante_monto = subtotal * Decimal("0.87")
    empresa_monto_subtotal = subtotal * Decimal("0.13")

    # Restaurante
    Movimiento.objects.create(
        wallet=restaurante_wallet,
        tipo="ingreso",
        monto=restaurante_monto,
        descripcion=f"Ingreso por orden #{orden.numero_orden} (subtotal)"
    )
    restaurante_wallet.saldo += restaurante_monto
    restaurante_wallet.save(update_fields=["saldo"])

    # Empresa (por subtotal)
    if empresa_wallet:
        Movimiento.objects.create(
            wallet=empresa_wallet,
            tipo="ingreso",
            monto=empresa_monto_subtotal,
            descripcion=f"Ingreso empresa por orden #{orden.numero_orden} (13% subtotal)"
        )
        empresa_wallet.saldo += empresa_monto_subtotal
        empresa_wallet.save(update_fields=["saldo"])

    # ==== ENVÍO ====
    empresa_envio = Decimal("0.00")
    conductor_envio = Decimal("0.00")

    if costo_envio > 0:
        primer_km = Decimal("1.00")
        if costo_envio >= primer_km:
            conductor_primer_km = Decimal("0.75")
            empresa_primer_km = Decimal("0.25")
            restante_envio = costo_envio - primer_km
        else:
            conductor_primer_km = costo_envio * Decimal("0.75")
            empresa_primer_km = costo_envio * Decimal("0.25")
            restante_envio = Decimal("0.00")

        # cálculo de tramos adicionales
        if restante_envio > 0:
            km_adicionales = restante_envio / Decimal("0.45")
            conductor_extra = km_adicionales * Decimal("0.20")
            empresa_extra = km_adicionales * Decimal("0.25")
        else:
            conductor_extra = Decimal("0.00")
            empresa_extra = Decimal("0.00")

        conductor_envio = conductor_primer_km + conductor_extra
        empresa_envio = empresa_primer_km + empresa_extra

        # Crear movimientos si hay wallets válidas
        if conductor_wallet:
            Movimiento.objects.create(
                wallet=conductor_wallet,
                tipo="ingreso",
                monto=conductor_envio,
                descripcion=f"Pago delivery por orden #{orden.numero_orden}"
            )
            conductor_wallet.saldo += conductor_envio
            conductor_wallet.save(update_fields=["saldo"])

        if empresa_wallet:
            Movimiento.objects.create(
                wallet=empresa_wallet,
                tipo="ingreso",
                monto=empresa_envio,
                descripcion=f"Ingreso empresa por envío orden #{orden.numero_orden}"
            )
            empresa_wallet.saldo += empresa_envio
            empresa_wallet.save(update_fields=["saldo"])

    # ==== IMPUESTO ====
    empresa_impuesto = impuesto
    if empresa_wallet and impuesto > 0:
        Movimiento.objects.create(
            wallet=empresa_wallet,
            tipo="ingreso",
            monto=empresa_impuesto,
            descripcion=f"Impuesto por orden #{orden.numero_orden}"
        )
        empresa_wallet.saldo += empresa_impuesto
        empresa_wallet.save(update_fields=["saldo"])

    # ==== AUDITORÍAS ====
    # Restaurante
    registrar_auditoria(
        usuario=orden.restaurante.usuario,
        accion="ingreso_wallet",
        descripcion=f"Se acreditaron {restaurante_monto} por la orden #{orden.numero_orden}",
        modelo_afectado="Wallet"
    )

    # Conductor
    if conductor_wallet:
        registrar_auditoria(
            usuario=orden.conductor.usuario,
            accion="ingreso_wallet",
            descripcion=f"Se acreditaron {conductor_envio} por la orden #{orden.numero_orden}",
            modelo_afectado="Wallet"
        )

    # Empresa
    if empresa_wallet and admin_user:
        total_empresa = empresa_monto_subtotal + empresa_envio + empresa_impuesto
        registrar_auditoria(
            usuario=admin_user,
            accion="ingreso_wallet",
            descripcion=f"Se acreditaron {total_empresa} por la orden #{orden.numero_orden}",
            modelo_afectado="Wallet"
        )

    # Marcar la orden como ya procesada
    orden.movimientos_generados = True
    orden.save(update_fields=["movimientos_generados"])

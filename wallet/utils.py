from wallet.models import Movimiento
from auditoria.services import registrar_auditoria

def asignar_pago_wallet_conductor(orden):
    conductor = orden.conductor
    if not conductor or not hasattr(conductor, 'wallet'):
        return

    monto = orden.total * 0.8  # Ejemplo: 80% del total para el conductor
    wallet = conductor.wallet

    Movimiento.objects.create(
        wallet=wallet,
        tipo='ingreso',
        monto=monto,
        descripcion=f'Ingreso por orden #{orden.id}'
    )

    wallet.saldo += monto
    wallet.save()

    registrar_auditoria(
        usuario=conductor,
        accion='ingreso_wallet',
        descripcion=f'Se ingresaron {monto} por la orden #{orden.id}',
        modelo_afectado='Wallet',
        id_objeto=wallet.id
    )

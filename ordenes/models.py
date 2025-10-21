from django.db import models
from core.models import Usuario, Conductor
from restaurantes.models import Restaurante
from decimal import Decimal
import uuid

class EstadoOrden(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField()
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return self.nombre

class Orden(models.Model):
    numero_orden = models.PositiveIntegerField(unique=True, editable=False, null=True, blank=True)
    cliente = models.ForeignKey(Usuario,null=True, blank=True,related_name='ordenes_cliente',on_delete=models.PROTECT,limit_choices_to={'rol__nombre': 'cliente'})
    restaurante = models.ForeignKey(Restaurante, on_delete=models.PROTECT)
    conductor = models.ForeignKey(Conductor,null=True, blank=True,related_name='ordenes_cliente',on_delete=models.PROTECT)
    estado = models.ForeignKey(EstadoOrden, on_delete=models.PROTECT)
    metodo_pago = models.ForeignKey("pagos.MetodoPago", on_delete=models.PROTECT)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    impuesto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    direccion_entrega = models.TextField(null=True, blank=True)
    latitud = models.DecimalField(max_digits=20, decimal_places=18, null=True, blank=True)
    longitud = models.DecimalField(max_digits=20, decimal_places=18, null=True, blank=True)
    limite_aceptacion = models.DateTimeField(null=True, blank=True)
    costo_envio = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    movimientos_generados = models.BooleanField(default=False)

    def __str__(self):
        return f"Orden #{self.numero_orden or self.id} - {self.cliente.nombre if self.cliente else 'Sin cliente'}"

    def save(self, *args, **kwargs):
        if self.numero_orden is None:
            ultimo = Orden.objects.aggregate(models.Max("numero_orden"))["numero_orden__max"] or 0
            self.numero_orden = ultimo + 1
        super().save(*args, **kwargs)

    def calcular_total(self):
        """
        Calcula subtotal, impuesto y total considerando:
        - Detalles de orden (incluyendo extras)
        - Descuento
        - Costo de envío
        """
        subtotal = Decimal("0.00")
        descuento_total = Decimal("0.00")

        for detalle in self.detalles.all():
            detalle.calcular_subtotal()  # ← recalcula subtotal (base + extras)
            subtotal += detalle.subtotal
            descuento_total += detalle.descuento

        base_imponible = subtotal - descuento_total
        impuesto = base_imponible * Decimal("0.16")  # IVA 16%
        costo_envio = self.costo_envio or Decimal("0.00")
        total = base_imponible + impuesto + costo_envio

        self.subtotal = subtotal
        self.descuento = descuento_total
        self.impuesto = impuesto
        self.total = total
        self.save(update_fields=["subtotal", "descuento", "impuesto", "total"])

        return self.total



class DetalleOrden(models.Model):
    orden = models.ForeignKey(Orden, related_name='detalles', on_delete=models.CASCADE)
    plato = models.ForeignKey('restaurantes.Plato', on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    extras = models.ManyToManyField('restaurantes.OpcionPlato', blank=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def calcular_subtotal(self, guardar=True):
        """
        Calcula el subtotal del detalle considerando:
        - Precio del plato
        - Precio de los extras
        - Cantidad
        """
        from decimal import Decimal

        total_extras = Decimal("0.00")
        for extra in self.extras.all():
            total_extras += extra.precio_adicional

        # Aplica descuento si el plato tiene precio especial
        if self.plato.precio_descuento and self.plato.precio_descuento < self.plato.precio:
            self.precio_unitario = self.plato.precio_descuento
            self.descuento = (self.plato.precio - self.plato.precio_descuento) * self.cantidad
        else:
            self.precio_unitario = self.plato.precio
            self.descuento = Decimal("0.00")

        self.subtotal = (self.precio_unitario + total_extras) * self.cantidad

        if guardar:
            super().save(update_fields=["precio_unitario", "subtotal", "descuento"])

        return self.subtotal

    def save(self, *args, **kwargs):
        # Si el plato tiene un precio de descuento válido, se aplica
        if self.plato.precio_descuento and self.plato.precio_descuento < self.plato.precio:
            self.precio_unitario = self.plato.precio_descuento
            self.descuento = (self.plato.precio - self.plato.precio_descuento) * self.cantidad
        else:
            self.precio_unitario = self.plato.precio
            self.descuento = 0

        self.subtotal = Decimal(self.precio_unitario) * self.cantidad
        super().save(*args, **kwargs)

        # Recalcular total de la orden
        self.orden.calcular_total()

    def delete(self, *args, **kwargs):
        orden = self.orden
        super().delete(*args, **kwargs)
        orden.calcular_total()

    def __str__(self):
        return f"{self.cantidad} x {self.plato.nombre} (Orden #{self.orden.id})"

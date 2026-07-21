from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.db import models

from features.orders.infrastructure.models import Order
from features.stores.domain.value_objects import GeoLocation


class DeliveryTracking(models.Model):
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="delivery_tracking",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "delivery_deliverytracking"
        verbose_name = "seguimiento de entrega"
        verbose_name_plural = "seguimientos de entrega"

    def __str__(self) -> str:
        return f"Tracking pedido #{self.order_id}"


class TrackingPoint(models.Model):
    tracking = models.ForeignKey(
        DeliveryTracking,
        on_delete=models.CASCADE,
        related_name="points",
    )
    location = gis_models.PointField(srid=4326)
    sequence = models.PositiveIntegerField()
    recorded_at = models.DateTimeField()

    class Meta:
        db_table = "delivery_trackingpoint"
        verbose_name = "punto de tracking"
        verbose_name_plural = "puntos de tracking"
        ordering = ["sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["tracking", "sequence"],
                name="uniq_delivery_tracking_point_sequence",
            )
        ]

    def __str__(self) -> str:
        return f"Punto #{self.sequence} — pedido #{self.tracking.order_id}"

    def set_location(self, geo: GeoLocation) -> None:
        self.location = Point(geo.longitude, geo.latitude, srid=4326)

    @property
    def latitude(self) -> float:
        return self.location.y

    @property
    def longitude(self) -> float:
        return self.location.x


class DriverOfferRejection(models.Model):
    """Rechazo de oferta: no re-ofrecer el mismo pedido al mismo conductor."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="offer_rejections",
    )
    driver = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.CASCADE,
        related_name="offer_rejections",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "delivery_driverofferrejection"
        verbose_name = "rechazo de oferta"
        verbose_name_plural = "rechazos de oferta"
        constraints = [
            models.UniqueConstraint(
                fields=["order", "driver"],
                name="uniq_delivery_offer_rejection_order_driver",
            )
        ]

    def __str__(self) -> str:
        return f"Reject order={self.order_id} driver={self.driver_id}"


def proof_photo_upload_to(instance: "ProofOfDelivery", filename: str) -> str:
    extension = filename.rsplit(".", 1)[-1]
    return f"delivery/proof/order_{instance.order_id}.{extension}"


class ProofOfDelivery(models.Model):
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="proof_of_delivery",
    )
    driver = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.CASCADE,
        related_name="proofs_of_delivery",
    )
    photo = models.ImageField(upload_to=proof_photo_upload_to, blank=True, null=True)
    signature_data = models.TextField(blank=True, default="")
    notes = models.TextField(blank=True, default="")
    delivered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "delivery_proof_of_delivery"
        verbose_name = "prueba de entrega"
        verbose_name_plural = "pruebas de entrega"

    def __str__(self) -> str:
        return f"Proof pedido #{self.order_id}"

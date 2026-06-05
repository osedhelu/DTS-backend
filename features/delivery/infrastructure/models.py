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

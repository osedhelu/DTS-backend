from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.db import models

from features.accounts.infrastructure.models import CustomUser
from features.stores.domain.entities import StoreStatus, StoreVertical
from features.stores.domain.value_objects import GeoLocation


def store_logo_upload_to(instance: "Store", filename: str) -> str:
    extension = filename.rsplit(".", 1)[-1]
    store_key = instance.pk or "new"
    return f"stores/{store_key}/logo.{extension}"


class Store(models.Model):
    owner = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="stores",
    )
    name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=10,
        choices=[(status.value, status.value) for status in StoreStatus],
        default=StoreStatus.CLOSED,
    )
    vertical = models.CharField(
        max_length=10,
        choices=[(vertical.value, vertical.value) for vertical in StoreVertical],
        default=StoreVertical.FOOD,
    )
    location = gis_models.PointField(srid=4326)
    address = models.TextField(blank=True)
    description = models.TextField(blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    logo = models.ImageField(upload_to=store_logo_upload_to, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    use_schedule = models.BooleanField(
        default=False,
        help_text="Si True, el estado open/closed se sincroniza con horarios.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "stores_store"
        verbose_name = "comercio"
        verbose_name_plural = "comercios"

    def __str__(self) -> str:
        return self.name

    def set_location(self, geo: GeoLocation) -> None:
        self.location = Point(geo.longitude, geo.latitude, srid=4326)

    @property
    def latitude(self) -> float:
        return self.location.y

    @property
    def longitude(self) -> float:
        return self.location.x


class StoreOpeningHours(models.Model):
    """Horario semanal de apertura por día (0=lunes … 6=domingo)."""

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="opening_hours",
    )
    day_of_week = models.PositiveSmallIntegerField()
    open_time = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)
    is_closed = models.BooleanField(default=False)

    class Meta:
        db_table = "stores_opening_hours"
        verbose_name = "horario de tienda"
        verbose_name_plural = "horarios de tienda"
        constraints = [
            models.UniqueConstraint(
                fields=["store", "day_of_week"],
                name="unique_opening_hours_per_day",
            ),
        ]
        ordering = ["day_of_week"]

    def __str__(self) -> str:
        if self.is_closed:
            return f"{self.store.name} — día {self.day_of_week}: cerrado"
        return f"{self.store.name} — día {self.day_of_week}: {self.open_time}-{self.close_time}"


class DeliveryZone(models.Model):
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="delivery_zones",
    )
    name = models.CharField(max_length=100, default="Principal")
    center_latitude = models.FloatField()
    center_longitude = models.FloatField()
    radius_km = models.DecimalField(max_digits=8, decimal_places=2, default=5)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "stores_delivery_zone"
        verbose_name = "zona de entrega"
        verbose_name_plural = "zonas de entrega"

    def __str__(self) -> str:
        return f"{self.store.name} — {self.name} ({self.radius_km} km)"


class StoreReview(models.Model):
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    customer = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.CASCADE,
        related_name="store_reviews",
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviews",
    )
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "stores_review"
        verbose_name = "reseña"
        verbose_name_plural = "reseñas"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name="store_review_rating_range",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.store.name} — {self.rating}★"

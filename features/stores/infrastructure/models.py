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

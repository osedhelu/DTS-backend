from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.db import models

from features.accounts.infrastructure.models import CustomUser
from features.stores.domain.entities import StoreStatus
from features.stores.domain.value_objects import GeoLocation


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
    location = gis_models.PointField(srid=4326)
    address = models.TextField(blank=True)
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

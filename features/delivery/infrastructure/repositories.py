from features.delivery.domain.entities import DeliveryTracking, TrackingPoint
from features.delivery.infrastructure.models import DeliveryTracking as DeliveryTrackingModel
from features.delivery.infrastructure.models import TrackingPoint as TrackingPointModel
from features.stores.domain.value_objects import GeoLocation


def _tracking_to_entity(model: DeliveryTrackingModel) -> DeliveryTracking:
    points = [
        TrackingPoint(
            id=point.id,
            latitude=point.latitude,
            longitude=point.longitude,
            sequence=point.sequence,
            recorded_at=point.recorded_at,
        )
        for point in model.points.order_by("sequence")
    ]
    return DeliveryTracking(
        id=model.id,
        order_id=model.order_id,
        points=points,
    )


class DjangoDeliveryTrackingRepository:
    def get_by_order_id(self, order_id: int) -> DeliveryTracking | None:
        try:
            model = DeliveryTrackingModel.objects.prefetch_related("points").get(
                order_id=order_id
            )
        except DeliveryTrackingModel.DoesNotExist:
            return None
        return _tracking_to_entity(model)

    def get_or_create(self, order_id: int) -> DeliveryTracking:
        model, _ = DeliveryTrackingModel.objects.get_or_create(order_id=order_id)
        model = DeliveryTrackingModel.objects.prefetch_related("points").get(pk=model.pk)
        return _tracking_to_entity(model)

    def save(self, tracking: DeliveryTracking) -> DeliveryTracking:
        model = DeliveryTrackingModel.objects.get(order_id=tracking.order_id)

        for point in tracking.points:
            if point.id is not None:
                continue

            point_model = TrackingPointModel(
                tracking=model,
                sequence=point.sequence,
                recorded_at=point.recorded_at,
            )
            point_model.set_location(
                GeoLocation(latitude=point.latitude, longitude=point.longitude)
            )
            point_model.save()

        model = DeliveryTrackingModel.objects.prefetch_related("points").get(pk=model.pk)
        return _tracking_to_entity(model)

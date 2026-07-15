from features.delivery.infrastructure.models import DriverOfferRejection


class RejectOfferUseCase:
    def execute(self, order_id: int, driver_id: int) -> None:
        DriverOfferRejection.objects.get_or_create(
            order_id=order_id,
            driver_id=driver_id,
        )

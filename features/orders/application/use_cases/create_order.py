from decimal import Decimal

from features.marketing.domain.entities import Coupon
from features.marketing.domain.exceptions import CouponNotApplicableError
from features.marketing.domain.services import CouponDiscountCalculator
from features.marketing.infrastructure.models import CouponModel
from features.orders.application.dto import CreateOrderDTO
from features.orders.domain.entities import Order, OrderItem
from features.orders.domain.exceptions import DomainValidationError, EmptyCartError
from features.orders.domain.repositories import OrderRepository
from features.orders.domain.value_objects import OrderStatus, OrderType
from features.payments.infrastructure.models import StorePaymentMethod
from features.products.domain.exceptions import InsufficientStockError, ProductNotFoundError
from features.products.domain.repositories import ProductRepository
from features.products.domain.services import StockValidator
from features.stores.domain.exceptions import StoreNotFoundError
from features.stores.domain.repositories import StoreRepository
from features.stores.infrastructure.operation_views import build_public_store_detail


class CreateOrderUseCase:
    def __init__(
        self,
        order_repository: OrderRepository,
        product_repository: ProductRepository,
        store_repository: StoreRepository,
    ) -> None:
        self._order_repository = order_repository
        self._product_repository = product_repository
        self._store_repository = store_repository

    def execute(self, dto: CreateOrderDTO) -> Order:
        if not dto.items:
            raise EmptyCartError("No se puede crear un pedido sin ítems")

        store = self._store_repository.get_by_id(dto.store_id)
        if store is None:
            raise StoreNotFoundError(f"Comercio {dto.store_id} no encontrado")

        if dto.latitude is not None and dto.longitude is not None:
            detail = build_public_store_detail(
                dto.store_id,
                customer_lat=dto.latitude,
                customer_lng=dto.longitude,
            )
            if not detail["accepts_orders"]:
                if not detail["is_open"]:
                    raise DomainValidationError("El comercio está cerrado en este momento")
                if not detail.get("in_delivery_zone", True):
                    raise DomainValidationError(
                        "Tu dirección está fuera de la zona de entrega"
                    )

        order_items: list[OrderItem] = []
        for line in dto.items:
            product = self._product_repository.get_by_id(line.product_id)
            if product is None or product.store_id != dto.store_id:
                raise ProductNotFoundError(
                    f"Producto {line.product_id} no encontrado en este comercio"
                )
            if not product.is_active:
                raise ProductNotFoundError(
                    f"Producto '{product.name}' no está disponible"
                )

            StockValidator.validate(product, line.quantity)

            order_items.append(
                OrderItem(
                    product_id=product.id,
                    product_name=product.name,
                    unit_price=product.price,
                    quantity=line.quantity,
                )
            )

        gross_total = sum((item.subtotal for item in order_items), Decimal("0"))
        discount = Decimal("0")
        coupon_code = (dto.coupon_code or "").strip().upper()
        if coupon_code:
            discount = self._apply_coupon(coupon_code, gross_total)

        payment_status = "pending"
        payment_method_id = dto.payment_method_id
        if payment_method_id is not None:
            method = StorePaymentMethod.objects.filter(
                pk=payment_method_id,
                store_id=dto.store_id,
                is_active=True,
            ).first()
            if method is None:
                raise DomainValidationError("Método de pago inválido")
            if method.method_type == "cash":
                payment_status = "cash_on_delivery"

        payload: dict = {
            "customer_id": dto.customer_id,
            "store_id": dto.store_id,
            "status": OrderStatus.CREATED,
            "order_type": OrderType.DELIVERY,
            "items": [
                {
                    "product_id": item.product_id,
                    "product_name": item.product_name,
                    "unit_price": item.unit_price,
                    "quantity": item.quantity,
                }
                for item in order_items
            ],
            "payment_method_id": payment_method_id,
            "payment_status": payment_status,
            "coupon_code": coupon_code,
            "discount_amount": discount,
        }
        if dto.delivery_address:
            payload["service_address"] = dto.delivery_address.strip()
        if dto.customer_notes:
            payload["customer_notes"] = dto.customer_notes.strip()
        if dto.latitude is not None:
            payload["service_latitude"] = dto.latitude
        if dto.longitude is not None:
            payload["service_longitude"] = dto.longitude

        return self._order_repository.create(payload)

    def _apply_coupon(self, code: str, order_total: Decimal) -> Decimal:
        model = CouponModel.objects.filter(code__iexact=code).first()
        if model is None:
            raise DomainValidationError("Cupón no encontrado")

        coupon = Coupon(
            code=model.code,
            discount_type=model.discount_type,
            discount_value=model.discount_value,
            min_order_total=model.min_order_total,
            max_uses=model.max_uses,
            used_count=model.used_count,
            valid_from=model.valid_from,
            valid_until=model.valid_until,
            is_active=model.is_active,
        )
        try:
            return CouponDiscountCalculator.calculate(order_total, coupon)
        except CouponNotApplicableError as exc:
            raise DomainValidationError(str(exc)) from exc

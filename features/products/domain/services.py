from features.products.domain.entities import Product
from features.products.domain.exceptions import InsufficientStockError


class StockValidator:
    """Valida disponibilidad de inventario al vender o reservar un ítem."""

    @staticmethod
    def validate(product: Product, quantity: int) -> None:
        if not product.tracks_stock:
            return

        if quantity <= 0:
            raise InsufficientStockError(
                f"La cantidad debe ser positiva, recibida: {quantity}"
            )

        if product.stock < quantity:
            raise InsufficientStockError(
                f"Stock insuficiente para '{product.name}': "
                f"disponible {product.stock}, solicitado {quantity}"
            )

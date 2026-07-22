from decimal import Decimal

from features.cart.infrastructure.models import Cart
from features.products.infrastructure.repositories import DjangoProductRepository


def serialize_cart(cart: Cart | None) -> dict:
    if cart is None or cart.store_id is None:
        return {
            "store_id": None,
            "store_name": "",
            "items": [],
            "item_count": 0,
            "total": "0.00",
        }

    items = list(cart.items.select_related("product").all())
    product_ids = [item.product_id for item in items]
    image_urls = DjangoProductRepository().primary_image_urls_for_products(product_ids)

    serialized_items = []
    total = Decimal("0")
    item_count = 0
    for item in items:
        product = item.product
        line_total = product.price * item.quantity
        total += line_total
        item_count += item.quantity
        serialized_items.append(
            {
                "product_id": product.id,
                "name": product.name,
                "price": str(product.price),
                "quantity": item.quantity,
                "notes": item.notes or "",
                "store_id": product.store_id,
                "product_type": product.product_type,
                "primary_image_url": image_urls.get(product.id),
                "stock": product.stock,
            }
        )

    store_name = ""
    if cart.store_id is not None:
        store_name = getattr(cart.store, "name", "") or ""

    return {
        "store_id": cart.store_id,
        "store_name": store_name,
        "items": serialized_items,
        "item_count": item_count,
        "total": f"{total:.2f}",
    }

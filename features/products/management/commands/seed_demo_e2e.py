from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.models import CustomUser, CustomerProfile, DriverProfile
from features.orders.domain.value_objects import OrderStatus, OrderType
from features.orders.infrastructure.models import Order, OrderItem
from features.payments.domain.entities import PaymentMethodType
from features.payments.infrastructure.models import StorePaymentMethod
from features.products.domain.entities import ProductType
from features.products.infrastructure.models import Category, Product, ProductIngredient, ProductVariant
from features.stores.infrastructure.models import DeliveryZone, Store


DEMO_PREFIX = "DEMO_E2E"


@dataclass(frozen=True)
class CategoryPlan:
    code: str
    name: str
    product_count: int
    field_config: dict[str, Any]
    subcategories: list[str]


CATEGORY_PLANS: list[CategoryPlan] = [
    CategoryPlan(
        code="A",
        name="Demo Cat A",
        product_count=10,
        field_config={
            "presentacion": {"mode": "single", "options": ["estandar", "premium"]},
            "extras": {"mode": "multi", "options": ["salsa", "queso", "hielo"]},
            "nota": "texto_libre",
        },
        subcategories=["A-Entradas", "A-Principales", "A-Bebidas"],
    ),
    CategoryPlan(
        code="B",
        name="Demo Cat B",
        product_count=21,
        field_config={
            "tamano": {"mode": "single", "options": ["S", "M", "L"]},
            "opciones": {"mode": "multi", "options": ["sin_azucar", "extra_salsa", "integral"]},
            "detalle": "texto_libre",
        },
        subcategories=["B-Combo", "B-Familiar", "B-Espacial"],
    ),
    CategoryPlan(
        code="C",
        name="Demo Cat C",
        product_count=8,
        field_config={
            "urgencia": {"mode": "single", "options": ["normal", "express"]},
            "incluye": {"mode": "multi", "options": ["insumos", "desplazamiento", "garantia"]},
            "observacion": "texto_libre",
        },
        subcategories=["C-Hogar", "C-Oficina"],
    ),
]


class Command(BaseCommand):
    help = "Genera datos demo E2E por tienda activa: categorias, productos, pagos y pedidos."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--orders-per-store",
            type=int,
            default=5,
            help="Cantidad de pedidos demo a crear por tienda activa.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simula la ejecución sin persistir cambios.",
        )
        parser.add_argument(
            "--reset-demo",
            action="store_true",
            help="Borra solo registros DEMO_E2E antes de generar.",
        )

    def handle(self, *args, **options) -> None:
        orders_per_store: int = max(0, int(options["orders_per_store"]))
        dry_run: bool = bool(options["dry_run"])
        reset_demo: bool = bool(options["reset_demo"])

        self.stdout.write(
            self.style.NOTICE(
                f"[seed_demo_e2e] inicio | dry_run={dry_run} reset_demo={reset_demo} "
                f"orders_per_store={orders_per_store}"
            )
        )

        stores = list(Store.objects.filter(is_active=True).select_related("owner").order_by("id"))
        if not stores:
            self.stdout.write(self.style.WARNING("No hay tiendas activas para procesar."))
            return

        customer = self._get_or_create_demo_customer()
        driver = self._get_or_create_demo_driver()

        with transaction.atomic():
            if reset_demo:
                self._reset_demo_data(stores, customer)

            report: list[dict[str, Any]] = []
            for store in stores:
                result = self._seed_store(store=store, customer=customer, driver=driver, orders_per_store=orders_per_store)
                report.append(result)

            if dry_run:
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING("Dry-run activo: rollback aplicado."))

        self._print_report(report, dry_run=dry_run)

    def _get_or_create_demo_customer(self) -> CustomUser:
        username = f"{DEMO_PREFIX.lower()}_customer"
        email = f"{DEMO_PREFIX.lower()}_customer@demo.local"
        user, created = CustomUser.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "role": UserRole.CUSTOMER,
                "email_verified": True,
            },
        )
        if created:
            user.set_password("demo12345")
            user.save(update_fields=["password"])
        elif user.role != UserRole.CUSTOMER:
            user.role = UserRole.CUSTOMER
            user.save(update_fields=["role", "updated_at"])

        CustomerProfile.objects.get_or_create(
            user=user,
            defaults={
                "full_name": "Cliente Demo E2E",
                "phone": "3000000000",
                "default_address": "Calle Demo # 00-00",
            },
        )
        return user

    def _get_or_create_demo_driver(self) -> CustomUser:
        username = f"{DEMO_PREFIX.lower()}_driver"
        email = f"{DEMO_PREFIX.lower()}_driver@demo.local"
        user, created = CustomUser.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "role": UserRole.DRIVER,
                "email_verified": True,
            },
        )
        if created:
            user.set_password("demo12345")
            user.save(update_fields=["password"])
        elif user.role != UserRole.DRIVER:
            user.role = UserRole.DRIVER
            user.save(update_fields=["role", "updated_at"])

        profile, _ = DriverProfile.objects.get_or_create(
            user=user,
            defaults={
                "phone": "3000000001",
                "full_name": "Conductor Demo E2E",
            },
        )
        profile.verification_status = "approved"
        profile.is_online = True
        profile.last_latitude = 4.711
        profile.last_longitude = -74.0721
        profile.onboarding_completed_at = profile.onboarding_completed_at or timezone.now()
        profile.save()
        return user

    def _reset_demo_data(self, stores: list[Store], customer: CustomUser) -> None:
        store_ids = [store.id for store in stores]
        product_qs = Product.objects.filter(store_id__in=store_ids, name__startswith=DEMO_PREFIX)
        product_ids = list(product_qs.values_list("id", flat=True))

        OrderItem.objects.filter(product_id__in=product_ids).delete()
        Order.objects.filter(
            customer=customer,
            store_id__in=store_ids,
            customer_notes__contains=DEMO_PREFIX,
        ).delete()
        ProductIngredient.objects.filter(product_id__in=product_ids).delete()
        ProductVariant.objects.filter(product_id__in=product_ids).delete()
        product_qs.delete()

        Category.objects.filter(store_id__in=store_ids, name__startswith=DEMO_PREFIX).delete()
        DeliveryZone.objects.filter(store_id__in=store_ids, name__startswith=DEMO_PREFIX).delete()

    def _seed_store(
        self,
        *,
        store: Store,
        customer: CustomUser,
        driver: CustomUser,
        orders_per_store: int,
    ) -> dict[str, Any]:
        zone, zone_created = DeliveryZone.objects.get_or_create(
            store=store,
            name=f"{DEMO_PREFIX}_Zona_Principal",
            defaults={
                "center_latitude": float(store.latitude),
                "center_longitude": float(store.longitude),
                "radius_km": Decimal("7.00"),
                "is_active": True,
            },
        )
        if not zone_created and not zone.is_active:
            zone.is_active = True
            zone.save(update_fields=["is_active", "updated_at"])

        payment_created = self._ensure_payment_methods(store)

        categories_created = 0
        products_created = 0
        services_created = 0
        physical_created = 0
        product_ids: list[int] = []

        for plan in CATEGORY_PLANS:
            parent, parent_created = Category.objects.get_or_create(
                store=store,
                parent=None,
                name=f"{DEMO_PREFIX}_{plan.name}",
                defaults={"field_config": plan.field_config},
            )
            if parent_created:
                categories_created += 1
            elif parent.field_config != plan.field_config:
                parent.field_config = plan.field_config
                parent.save(update_fields=["field_config", "updated_at"])

            children: list[Category] = []
            for sub_name in plan.subcategories:
                child, child_created = Category.objects.get_or_create(
                    store=store,
                    parent=parent,
                    name=f"{DEMO_PREFIX}_{sub_name}",
                    defaults={"field_config": {}},
                )
                children.append(child)
                if child_created:
                    categories_created += 1

            for idx in range(plan.product_count):
                product_type = ProductType.SERVICE if idx % 4 == 0 else ProductType.PHYSICAL
                subcategory = children[idx % len(children)]
                dynamic_values = self._build_dynamic_values(plan.code, idx)
                defaults = self._build_product_defaults(
                    store=store,
                    plan=plan,
                    idx=idx,
                    product_type=product_type,
                    dynamic_values=dynamic_values,
                )
                product_name = f"{DEMO_PREFIX}_{plan.code}_{idx + 1:02d}_{store.id}"

                product, created = Product.objects.get_or_create(
                    store=store,
                    name=product_name,
                    defaults=defaults | {"category": parent, "subcategory": subcategory},
                )

                if not created:
                    changed = False
                    for field, value in (defaults | {"category": parent, "subcategory": subcategory}).items():
                        if getattr(product, field) != value:
                            setattr(product, field, value)
                            changed = True
                    if changed:
                        product.save()
                else:
                    products_created += 1
                    if product_type == ProductType.SERVICE:
                        services_created += 1
                    else:
                        physical_created += 1

                product_ids.append(product.id)
                self._ensure_product_details(product, idx)

        orders_created = self._create_demo_orders(
            store=store,
            customer=customer,
            driver=driver,
            product_ids=product_ids,
            orders_per_store=orders_per_store,
        )

        return {
            "store_id": store.id,
            "store_name": store.name,
            "categories_created": categories_created,
            "products_created": products_created,
            "physical_products_created": physical_created,
            "service_products_created": services_created,
            "orders_created": orders_created,
            "payment_methods_created": payment_created,
        }

    def _build_dynamic_values(self, code: str, idx: int) -> dict[str, Any]:
        if code == "A":
            return {
                "presentacion": "premium" if idx % 2 == 0 else "estandar",
                "extras": ["salsa", "queso"] if idx % 3 == 0 else ["hielo"],
                "nota": f"nota demo {idx + 1}",
            }
        if code == "B":
            return {
                "tamano": ["S", "M", "L"][idx % 3],
                "opciones": ["sin_azucar", "extra_salsa"] if idx % 2 == 0 else ["integral"],
                "detalle": f"detalle demo {idx + 1}",
            }
        return {
            "urgencia": "express" if idx % 2 == 0 else "normal",
            "incluye": ["insumos", "garantia"] if idx % 3 == 0 else ["desplazamiento"],
            "observacion": f"observacion demo {idx + 1}",
        }

    def _build_product_defaults(
        self,
        *,
        store: Store,
        plan: CategoryPlan,
        idx: int,
        product_type: ProductType,
        dynamic_values: dict[str, Any],
    ) -> dict[str, Any]:
        is_service = product_type == ProductType.SERVICE
        base_price = Decimal("9000.00") + Decimal(idx * 1300) + Decimal(store.id % 11) * Decimal("75")
        return {
            "description": (
                f"Producto demo {plan.code}-{idx + 1} para pruebas E2E. "
                f"Incluye datos de ejemplo para checkout, pedidos y delivery."
            ),
            "price": base_price,
            "stock": 0 if is_service else (20 + (idx % 15)),
            "product_type": product_type,
            "requires_on_site_visit": is_service,
            "duration_minutes": 60 + (idx % 4) * 30 if is_service else None,
            "is_active": True,
            "dynamic_values": dynamic_values,
        }

    def _ensure_product_details(self, product: Product, idx: int) -> None:
        if product.product_type == ProductType.PHYSICAL:
            ProductVariant.objects.get_or_create(
                product=product,
                name="Unidad",
                defaults={
                    "price": product.price,
                    "sort_order": 0,
                },
            )
            ProductVariant.objects.get_or_create(
                product=product,
                name="Combo",
                defaults={
                    "price": product.price + Decimal("3500.00"),
                    "sort_order": 1,
                },
            )
            ProductIngredient.objects.get_or_create(
                product=product,
                name=f"Ingrediente base {idx % 7 + 1}",
                defaults={"is_allergen": idx % 5 == 0},
            )

    def _ensure_payment_methods(self, store: Store) -> int:
        created_count = 0
        for method_type, name, sort_order in (
            (PaymentMethodType.CASH.value, "Efectivo contra entrega", 10),
            (PaymentMethodType.SANDBOX.value, "Sandbox DTS", 20),
        ):
            _, created = StorePaymentMethod.objects.get_or_create(
                store=store,
                method_type=method_type,
                name=name,
                defaults={
                    "instructions": f"{DEMO_PREFIX}: metodo de prueba para compras E2E",
                    "is_active": True,
                    "sort_order": sort_order,
                },
            )
            if created:
                created_count += 1
        return created_count

    def _create_demo_orders(
        self,
        *,
        store: Store,
        customer: CustomUser,
        driver: CustomUser,
        product_ids: list[int],
        orders_per_store: int,
    ) -> int:
        if orders_per_store <= 0 or not product_ids:
            return 0

        physical_products = list(
            Product.objects.filter(id__in=product_ids, product_type=ProductType.PHYSICAL, is_active=True).order_by("id")
        )
        service_products = list(
            Product.objects.filter(id__in=product_ids, product_type=ProductType.SERVICE, is_active=True).order_by("id")
        )
        if not physical_products:
            return 0

        cash_method = StorePaymentMethod.objects.filter(
            store=store, method_type=PaymentMethodType.CASH.value, is_active=True
        ).first()
        sandbox_method = StorePaymentMethod.objects.filter(
            store=store, method_type=PaymentMethodType.SANDBOX.value, is_active=True
        ).first()

        created = 0
        for idx in range(orders_per_store):
            service_mode = bool(service_products) and idx % 3 == 0
            product = service_products[idx % len(service_products)] if service_mode else physical_products[idx % len(physical_products)]
            quantity = 1 + (idx % 2)
            order_type = OrderType.SERVICE if service_mode else OrderType.DELIVERY

            notes = f"{DEMO_PREFIX}: pedido tienda={store.id} n={idx + 1}"
            if Order.objects.filter(store=store, customer=customer, customer_notes=notes).exists():
                continue

            method = sandbox_method if idx % 2 == 0 and sandbox_method else cash_method
            payment_status = "paid" if method and method.method_type == PaymentMethodType.SANDBOX.value else "cash_on_delivery"
            status = OrderStatus.COMPLETED if service_mode else [OrderStatus.CREATED, OrderStatus.DRIVER_ASSIGNED, OrderStatus.DELIVERED][idx % 3]

            order = Order.objects.create(
                customer=customer,
                store=store,
                driver=driver if status in {OrderStatus.DRIVER_ASSIGNED, OrderStatus.DELIVERED} else None,
                status=status,
                order_type=order_type,
                service_address=f"Calle Demo {store.id} #{idx + 10}-00",
                customer_notes=notes,
                service_latitude=float(store.latitude),
                service_longitude=float(store.longitude),
                duration_minutes=90 if service_mode else None,
                payment_method=method,
                payment_status=payment_status,
                payment_reference=f"{DEMO_PREFIX}-{store.id}-{idx + 1}",
                paid_at=timezone.now() if payment_status == "paid" else None,
            )
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                unit_price=product.price,
                quantity=quantity,
            )
            order.total = order.compute_total()
            order.save(update_fields=["total", "updated_at"])
            created += 1

        return created

    def _print_report(self, report: list[dict[str, Any]], *, dry_run: bool) -> None:
        totals = {
            "categories_created": 0,
            "products_created": 0,
            "physical_products_created": 0,
            "service_products_created": 0,
            "orders_created": 0,
            "payment_methods_created": 0,
        }
        for row in report:
            self.stdout.write(
                f"Store[{row['store_id']}] {row['store_name']} | "
                f"cats+={row['categories_created']} products+={row['products_created']} "
                f"(physical={row['physical_products_created']} service={row['service_products_created']}) "
                f"orders+={row['orders_created']} payments+={row['payment_methods_created']}"
            )
            for key in totals:
                totals[key] += int(row[key])

        mode = "DRY-RUN" if dry_run else "APLICADO"
        self.stdout.write(
            self.style.SUCCESS(
                f"[seed_demo_e2e] {mode} | stores={len(report)} "
                f"cats+={totals['categories_created']} products+={totals['products_created']} "
                f"orders+={totals['orders_created']} payment_methods+={totals['payment_methods_created']}"
            )
        )

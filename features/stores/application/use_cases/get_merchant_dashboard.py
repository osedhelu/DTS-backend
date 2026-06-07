from datetime import date

from features.stores.domain.dashboard_services import MerchantDashboardAggregator
from features.stores.domain.exceptions import NotStoreOwnerError, StoreNotFoundError
from features.stores.domain.repositories import StoreRepository
from features.stores.infrastructure.merchant_dashboard_repository import (
    DjangoMerchantDashboardRepository,
)


class GetMerchantDashboardUseCase:
    def __init__(
        self,
        store_repository: StoreRepository,
        dashboard_repository: DjangoMerchantDashboardRepository | None = None,
    ) -> None:
        self._store_repository = store_repository
        self._dashboard_repository = dashboard_repository or DjangoMerchantDashboardRepository()

    def execute(self, *, store_id: int, owner_id: int, days: int = 30) -> dict:
        store = self._store_repository.get_by_id(store_id)
        if store is None:
            raise StoreNotFoundError(f"Comercio {store_id} no encontrado")
        if store.owner_id != owner_id:
            raise NotStoreOwnerError("No tienes permiso para ver este comercio")

        period_end = date.today()
        start_date, end_date, period_days = self._dashboard_repository.resolve_period(
            days,
            period_end=period_end,
        )

        completed_orders = self._dashboard_repository.get_completed_orders(
            store_id,
            start_date=start_date,
            end_date=end_date,
        )
        orders_today = self._dashboard_repository.count_completed_orders_on(
            store_id,
            start_date=period_end,
            end_date=period_end,
        )
        week_start = self._dashboard_repository.week_start(period_end)
        orders_this_week = self._dashboard_repository.count_completed_orders_on(
            store_id,
            start_date=week_start,
            end_date=period_end,
        )
        active_products = self._dashboard_repository.count_active_products(store_id)
        product_sales = self._dashboard_repository.get_product_sales(
            store_id,
            start_date=start_date,
            end_date=end_date,
        )

        metrics = MerchantDashboardAggregator.aggregate(
            store_id=store_id,
            period_days=period_days,
            period_end=period_end,
            completed_orders=completed_orders,
            orders_today=orders_today,
            orders_this_week=orders_this_week,
            active_products=active_products,
            product_sales=product_sales,
        )

        return {
            "store_id": metrics.store_id,
            "period_days": metrics.period_days,
            "total_sales": str(metrics.total_sales),
            "order_count": metrics.order_count,
            "orders_today": metrics.orders_today,
            "orders_this_week": metrics.orders_this_week,
            "average_ticket": str(metrics.average_ticket),
            "platform_commission_rate": str(metrics.platform_commission_rate),
            "platform_commission": str(metrics.platform_commission),
            "net_earnings": str(metrics.net_earnings),
            "active_products": metrics.active_products,
            "sales_series": [
                {"date": point.date.isoformat(), "total": str(point.total)}
                for point in metrics.sales_series
            ],
            "top_products": [
                {
                    "product_id": product.product_id,
                    "product_name": product.product_name,
                    "quantity_sold": product.quantity_sold,
                    "revenue": str(product.revenue),
                }
                for product in metrics.top_products
            ],
        }

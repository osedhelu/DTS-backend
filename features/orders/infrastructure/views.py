from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.pagination import paginate_list
from core.openapi import DetailErrorSerializer
from features.accounts.domain.entities import UserRole
from features.accounts.infrastructure.permissions import IsCustomer
from features.orders.application.dto import CreateOrderDTO, OrderLineDTO, TransitionOrderStatusDTO
from features.orders.domain.exceptions import (
    DomainValidationError,
    EmptyCartError,
    OrderNotFoundError,
    UnauthorizedOrderTransitionError,
)
from features.orders.domain.value_objects import OrderStatus
from features.products.domain.exceptions import InsufficientStockError, ProductNotFoundError
from features.stores.domain.exceptions import NotStoreOwnerError, StoreNotFoundError
from features.orders.infrastructure.serializers import (
    CreateOrderSerializer,
    CreateServiceOrderSerializer,
    CustomerOrderDetailSerializer,
    DriverOrderDetailSerializer,
    MerchantOrderSerializer,
    OrderSerializer,
    TransitionOrderSerializer,
    build_customer_order_detail_enrichment,
    build_driver_order_detail_enrichment,
    build_merchant_order_enrichment,
)


@extend_schema_view(
    get=extend_schema(responses={200: OrderSerializer(many=True)}),
    post=extend_schema(
        request=CreateOrderSerializer,
        responses={201: OrderSerializer, 400: DetailErrorSerializer, 404: DetailErrorSerializer},
    ),
)
class OrderListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsCustomer()]
        return [IsAuthenticated()]

    def get(self, request):
        from features.orders.infrastructure.repositories import (
            DjangoOrderRepository,
            _order_to_entity,
        )
        from features.orders.infrastructure.serializers import (
            MerchantOrderSerializer,
            OrderSerializer,
        )

        status_filter = request.query_params.get("status")
        parsed_status = OrderStatus(status_filter) if status_filter else None
        role = UserRole(request.user.role)
        repository = DjangoOrderRepository()

        if role == UserRole.MERCHANT:
            order_models = repository.list_models_for_user(
                request.user.id,
                role,
                status=parsed_status,
            )
            return paginate_list(
                request,
                order_models,
                lambda page: [
                    MerchantOrderSerializer(
                        _order_to_entity(model),
                        context={"enrichment": build_merchant_order_enrichment(model)},
                    ).data
                    for model in page
                ],
            )

        orders = repository.list_for_user(
            request.user.id,
            role,
            status=parsed_status,
        )
        return paginate_list(
            request,
            orders,
            lambda page: OrderSerializer(page, many=True).data,
        )

    def post(self, request):
        from features.orders.application.use_cases.create_order import CreateOrderUseCase
        from features.orders.infrastructure.repositories import DjangoOrderRepository
        from features.orders.infrastructure.serializers import CreateOrderSerializer, OrderSerializer
        from features.products.infrastructure.repositories import DjangoProductRepository
        from features.stores.infrastructure.repositories import DjangoStoreRepository

        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        use_case = CreateOrderUseCase(
            DjangoOrderRepository(),
            DjangoProductRepository(),
            DjangoStoreRepository(),
        )

        try:
            order = use_case.execute(
                CreateOrderDTO(
                    customer_id=request.user.id,
                    store_id=data["store_id"],
                    items=tuple(
                        OrderLineDTO(product_id=item["product_id"], quantity=item["quantity"])
                        for item in data["items"]
                    ),
                    delivery_address=data.get("delivery_address", ""),
                    customer_notes=data.get("customer_notes", ""),
                    latitude=data.get("latitude"),
                    longitude=data.get("longitude"),
                    payment_method_id=data.get("payment_method_id"),
                    coupon_code=data.get("coupon_code", ""),
                )
            )
        except EmptyCartError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except StoreNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except ProductNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except InsufficientStockError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except DomainValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        from features.cart.application.use_cases.clear_cart import clear_customer_cart

        clear_customer_cart(request.user.id)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    post=extend_schema(
        request=CreateServiceOrderSerializer,
        responses={201: OrderSerializer, 400: DetailErrorSerializer, 404: DetailErrorSerializer},
    ),
)
class ServiceOrderCreateView(APIView):
    permission_classes = [IsCustomer]

    def post(self, request):
        from features.orders.application.dto import CreateServiceOrderDTO, OrderLineDTO
        from features.orders.application.use_cases.create_service_order import (
            CreateServiceOrderUseCase,
        )
        from features.orders.infrastructure.repositories import DjangoOrderRepository
        from features.orders.infrastructure.serializers import (
            CreateServiceOrderSerializer,
            OrderSerializer,
        )
        from features.products.infrastructure.repositories import DjangoProductRepository
        from features.stores.infrastructure.repositories import DjangoStoreRepository

        serializer = CreateServiceOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        use_case = CreateServiceOrderUseCase(
            DjangoOrderRepository(),
            DjangoProductRepository(),
            DjangoStoreRepository(),
        )

        try:
            order = use_case.execute(
                CreateServiceOrderDTO(
                    customer_id=request.user.id,
                    store_id=data["store_id"],
                    items=tuple(
                        OrderLineDTO(product_id=item["product_id"], quantity=item["quantity"])
                        for item in data["items"]
                    ),
                    service_address=data["service_address"],
                    customer_notes=data.get("customer_notes", ""),
                    scheduled_at=data.get("scheduled_at"),
                    latitude=data.get("latitude"),
                    longitude=data.get("longitude"),
                    payment_method_id=data.get("payment_method_id"),
                    coupon_code=data.get("coupon_code", ""),
                )
            )
        except EmptyCartError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except StoreNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except ProductNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except DomainValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        from features.cart.application.use_cases.clear_cart import clear_customer_cart

        clear_customer_cart(request.user.id)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


def _user_can_view_order(user, order, role: UserRole) -> bool:
    if role == UserRole.SUPER_ADMIN:
        return True
    if order.customer_id == user.id:
        return True
    if order.driver_id == user.id:
        return True
    if role == UserRole.MERCHANT:
        from features.stores.infrastructure.models import Store

        return Store.objects.filter(id=order.store_id, owner_id=user.id).exists()
    return False


@extend_schema_view(
    get=extend_schema(
        responses={
            200: DriverOrderDetailSerializer,
            403: DetailErrorSerializer,
            404: DetailErrorSerializer,
        },
    ),
    patch=extend_schema(
        request=TransitionOrderSerializer,
        responses={
            200: OrderSerializer,
            400: DetailErrorSerializer,
            403: DetailErrorSerializer,
            404: DetailErrorSerializer,
        },
    ),
)
class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id: int):
        from features.orders.infrastructure.models import Order as OrderModel
        from features.orders.infrastructure.repositories import DjangoOrderRepository

        repository = DjangoOrderRepository()
        order = repository.get_by_id(order_id)
        if order is None:
            return Response(
                {"detail": f"Pedido {order_id} no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        role = UserRole(request.user.role)
        if not _user_can_view_order(request.user, order, role):
            return Response(
                {"detail": "No autorizado para ver este pedido"},
                status=status.HTTP_403_FORBIDDEN,
            )

        order_model = OrderModel.objects.select_related(
            "store",
            "customer__customer_profile",
            "driver__driver_profile",
        ).prefetch_related("items").get(pk=order_id)

        if role == UserRole.CUSTOMER:
            enrichment = build_customer_order_detail_enrichment(order_model)
            return Response(
                CustomerOrderDetailSerializer(order, context={"enrichment": enrichment}).data
            )

        if role == UserRole.MERCHANT:
            enrichment = build_merchant_order_enrichment(order_model)
            return Response(
                MerchantOrderSerializer(order, context={"enrichment": enrichment}).data
            )

        enrichment = build_driver_order_detail_enrichment(order_model)
        return Response(
            DriverOrderDetailSerializer(order, context={"enrichment": enrichment}).data
        )

    def patch(self, request, order_id: int):
        from features.orders.application.use_cases.transition_order_status import (
            TransitionOrderStatusUseCase,
        )
        from features.orders.infrastructure.repositories import DjangoOrderRepository
        from features.orders.infrastructure.serializers import OrderSerializer, TransitionOrderSerializer
        from features.stores.infrastructure.repositories import DjangoStoreRepository

        serializer = TransitionOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = TransitionOrderStatusUseCase(
            DjangoOrderRepository(),
            DjangoStoreRepository(),
        )

        try:
            order = use_case.execute(
                TransitionOrderStatusDTO(
                    order_id=order_id,
                    target_status=OrderStatus(serializer.validated_data["status"]),
                    actor_id=request.user.id,
                    actor_role=UserRole(request.user.role),
                )
            )
        except OrderNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except NotStoreOwnerError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except UnauthorizedOrderTransitionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except DomainValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(OrderSerializer(order).data)

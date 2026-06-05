from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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


class OrderListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsCustomer()]
        return [IsAuthenticated()]

    def get(self, request):
        from features.orders.infrastructure.repositories import DjangoOrderRepository
        from features.orders.infrastructure.serializers import OrderSerializer

        repository = DjangoOrderRepository()
        orders = repository.list_for_user(request.user.id, UserRole(request.user.role))
        return Response(OrderSerializer(orders, many=True).data)

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

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

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

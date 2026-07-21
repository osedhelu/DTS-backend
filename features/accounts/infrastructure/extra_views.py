"""Vistas adicionales: favoritos, retiros, verificación conductor."""

from decimal import Decimal

from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.openapi import DetailErrorSerializer
from features.accounts.infrastructure.models import (
    CustomUser,
    DriverPayoutRequest,
    DriverProfile,
    FavoriteStore,
)
from features.accounts.infrastructure.permissions import IsCustomer, IsDriver, IsSuperAdmin
from features.stores.infrastructure.serializers import StoreSerializer
from features.stores.infrastructure.repositories import DjangoStoreRepository


class FavoriteStoreSerializer(serializers.Serializer):
    store_id = serializers.IntegerField()
    created_at = serializers.DateTimeField(read_only=True)


class PayoutRequestSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("1"))


class DriverVerificationSerializer(serializers.Serializer):
    verification_status = serializers.ChoiceField(
        choices=["approved", "rejected"],
    )


@extend_schema_view(
    get=extend_schema(responses={200: StoreSerializer(many=True)}),
    post=extend_schema(request=FavoriteStoreSerializer, responses={201: FavoriteStoreSerializer}),
)
class FavoriteStoreListView(APIView):
    permission_classes = [IsCustomer]

    def get(self, request):
        favorites = FavoriteStore.objects.filter(user_id=request.user.id).select_related("store")
        repo = DjangoStoreRepository()
        stores = []
        for fav in favorites:
            store = repo.get_by_id(fav.store_id)
            if store is not None:
                stores.append(store)
        return Response(StoreSerializer(stores, many=True).data)

    def post(self, request):
        store_id = request.data.get("store_id")
        if not store_id:
            return Response({"detail": "store_id requerido"}, status=status.HTTP_400_BAD_REQUEST)
        fav, _ = FavoriteStore.objects.get_or_create(
            user_id=request.user.id,
            store_id=int(store_id),
        )
        return Response(
            {"store_id": fav.store_id, "created_at": fav.created_at},
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    delete=extend_schema(responses={204: None}),
)
class FavoriteStoreDetailView(APIView):
    permission_classes = [IsCustomer]

    def delete(self, request, store_id: int):
        deleted, _ = FavoriteStore.objects.filter(
            user_id=request.user.id, store_id=store_id
        ).delete()
        if not deleted:
            return Response({"detail": "No encontrado"}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    get=extend_schema(responses={200: PayoutRequestSerializer(many=True)}),
    post=extend_schema(request=PayoutRequestSerializer, responses={201: PayoutRequestSerializer}),
)
class DriverPayoutListView(APIView):
    permission_classes = [IsDriver]

    def get(self, request):
        rows = DriverPayoutRequest.objects.filter(driver_id=request.user.id).order_by(
            "-requested_at"
        )[:50]
        return Response(
            [
                {
                    "id": row.id,
                    "amount": str(row.amount),
                    "status": row.status,
                    "notes": row.notes,
                    "requested_at": row.requested_at,
                    "processed_at": row.processed_at,
                }
                for row in rows
            ]
        )

    def post(self, request):
        serializer = PayoutRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = DriverProfile.objects.filter(user_id=request.user.id).first()
        if profile is None or profile.verification_status != "approved":
            return Response(
                {"detail": "Conductor no verificado para retiros"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not profile.bank_account_number:
            return Response(
                {"detail": "Configura tus datos bancarios primero"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        payout = DriverPayoutRequest.objects.create(
            driver_id=request.user.id,
            amount=serializer.validated_data["amount"],
        )
        return Response(
            {
                "id": payout.id,
                "amount": str(payout.amount),
                "status": payout.status,
                "requested_at": payout.requested_at,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    patch=extend_schema(
        request=DriverVerificationSerializer,
        responses={200: DriverVerificationSerializer, 404: DetailErrorSerializer},
    ),
)
class AdminDriverVerificationView(APIView):
    permission_classes = [IsSuperAdmin]

    def patch(self, request, driver_id: int):
        serializer = DriverVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        status_value = serializer.validated_data["verification_status"]

        user = CustomUser.objects.filter(pk=driver_id, role="driver").first()
        if user is None:
            return Response({"detail": "Conductor no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        profile, _ = DriverProfile.objects.get_or_create(
            user=user,
            defaults={"phone": user.email},
        )
        profile.verification_status = status_value
        profile.verified_at = timezone.now() if status_value == "approved" else None
        profile.save(update_fields=["verification_status", "verified_at", "updated_at"])

        from features.analytics.infrastructure.audit_views import record_audit

        record_audit(
            user_id=request.user.id,
            action="driver_verification_updated",
            resource_type="driver",
            resource_id=str(driver_id),
            metadata={"verification_status": status_value},
        )

        return Response({"driver_id": driver_id, "verification_status": profile.verification_status})

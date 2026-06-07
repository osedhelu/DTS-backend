from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.pagination import paginate_list
from features.accounts.application.use_cases.list_admin_merchants import (
    AdminMerchantRow,
    ListAdminMerchantsUseCase,
)
from features.accounts.infrastructure.permissions import IsSuperAdmin


class AdminMerchantSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email_verified = serializers.BooleanField()
    user_is_active = serializers.BooleanField()
    business_name = serializers.CharField()
    phone = serializers.CharField()
    store_id = serializers.IntegerField()
    store_name = serializers.CharField()
    store_vertical = serializers.CharField()
    store_is_active = serializers.BooleanField()
    registered_at = serializers.DateTimeField()


def _parse_bool_param(value: str | None) -> bool | None:
    if value is None or value == "":
        return None
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    return None


def _serialize_row(row: AdminMerchantRow) -> dict:
    return AdminMerchantSerializer(
        {
            "user_id": row.user_id,
            "email": row.email,
            "first_name": row.first_name,
            "last_name": row.last_name,
            "email_verified": row.email_verified,
            "user_is_active": row.user_is_active,
            "business_name": row.business_name,
            "phone": row.phone,
            "store_id": row.store_id,
            "store_name": row.store_name,
            "store_vertical": row.store_vertical,
            "store_is_active": row.store_is_active,
            "registered_at": row.registered_at,
        }
    ).data


@extend_schema_view(
    get=extend_schema(
        responses={200: AdminMerchantSerializer(many=True)},
    ),
)
class AdminMerchantListView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        use_case = ListAdminMerchantsUseCase()
        merchants = use_case.execute(
            email_verified=_parse_bool_param(request.query_params.get("email_verified")),
            user_is_active=_parse_bool_param(request.query_params.get("is_active")),
        )
        return paginate_list(
            request,
            merchants,
            lambda page: [_serialize_row(row) for row in page],
        )

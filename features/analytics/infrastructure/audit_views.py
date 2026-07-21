"""Registro de auditoría para acciones admin."""

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from features.accounts.infrastructure.permissions import IsSuperAdmin
from features.analytics.infrastructure.models import AuditLog


class AuditLogSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    action = serializers.CharField()
    resource_type = serializers.CharField()
    resource_id = serializers.CharField()
    metadata = serializers.JSONField()
    user_id = serializers.IntegerField(allow_null=True)
    created_at = serializers.DateTimeField()


def record_audit(
    *,
    user_id: int | None,
    action: str,
    resource_type: str,
    resource_id: str = "",
    metadata: dict | None = None,
) -> AuditLog:
    return AuditLog.objects.create(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata=metadata or {},
    )


@extend_schema_view(
    get=extend_schema(responses={200: AuditLogSerializer(many=True)}),
)
class AuditLogListView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        logs = AuditLog.objects.all().order_by("-created_at")[:100]
        return Response(
            [
                {
                    "id": log.id,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "metadata": log.metadata,
                    "user_id": log.user_id,
                    "created_at": log.created_at,
                }
                for log in logs
            ]
        )

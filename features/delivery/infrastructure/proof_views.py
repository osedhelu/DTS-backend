"""Prueba de entrega (foto/firma)."""

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.media_urls import build_public_media_url
from core.openapi import DetailErrorSerializer
from features.accounts.infrastructure.permissions import IsDriver
from features.delivery.application.use_cases.submit_proof_of_delivery import (
    MissingDeliveryPhotoError,
    SubmitProofOfDeliveryUseCase,
)
from features.delivery.infrastructure.models import ProofOfDelivery
from features.orders.domain.exceptions import OrderNotFoundError


class ProofOfDeliverySerializer(serializers.Serializer):
    photo = serializers.ImageField(required=True)
    signature_data = serializers.CharField(required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")


@extend_schema_view(
    post=extend_schema(
        request=ProofOfDeliverySerializer,
        responses={201: ProofOfDeliverySerializer, 403: DetailErrorSerializer},
    ),
    get=extend_schema(responses={200: ProofOfDeliverySerializer, 404: DetailErrorSerializer}),
)
class ProofOfDeliveryView(APIView):
    permission_classes = [IsDriver]

    def post(self, request, order_id: int):
        serializer = ProofOfDeliverySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = SubmitProofOfDeliveryUseCase().execute(
                order_id=order_id,
                driver_id=request.user.id,
                photo=serializer.validated_data.get("photo"),
                signature_data=serializer.validated_data.get("signature_data", ""),
                notes=serializer.validated_data.get("notes", ""),
            )
        except OrderNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except MissingDeliveryPhotoError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_201_CREATED)

    def get(self, request, order_id: int):
        proof = ProofOfDelivery.objects.filter(
            order_id=order_id, driver_id=request.user.id
        ).first()
        if proof is None:
            return Response({"detail": "No encontrado"}, status=status.HTTP_404_NOT_FOUND)
        return Response(self._serialize(proof))

    @staticmethod
    def _serialize(proof: ProofOfDelivery) -> dict:
        return {
            "order_id": proof.order_id,
            "photo_url": build_public_media_url(proof.photo.url if proof.photo else ""),
            "signature_data": proof.signature_data,
            "notes": proof.notes,
            "delivered_at": proof.delivered_at,
        }

"""Caso de uso: prueba de entrega → mensaje de chat con foto → cierre del chat."""

from __future__ import annotations

from django.core.files.uploadedfile import UploadedFile

from core.media_urls import build_public_media_url
from features.chat.application.use_cases.send_order_message import (
    SendOrderMessageUseCase,
    broadcast_chat_closed,
)
from features.chat.infrastructure.models import ChatMessageType
from features.delivery.infrastructure.models import ProofOfDelivery
from features.orders.domain.exceptions import OrderNotFoundError
from features.orders.domain.value_objects import OrderStatus
from features.orders.infrastructure.models import Order


class MissingDeliveryPhotoError(ValueError):
    pass


class SubmitProofOfDeliveryUseCase:
    def execute(
        self,
        *,
        order_id: int,
        driver_id: int,
        photo: UploadedFile | None,
        signature_data: str = "",
        notes: str = "",
    ) -> dict:
        if photo is None:
            raise MissingDeliveryPhotoError(
                "La foto de entrega es obligatoria para marcar el pedido como entregado"
            )

        order = (
            Order.objects.select_related("store")
            .filter(pk=order_id, driver_id=driver_id)
            .first()
        )
        if order is None:
            raise OrderNotFoundError("Pedido no encontrado")

        proof, _ = ProofOfDelivery.objects.update_or_create(
            order_id=order_id,
            defaults={
                "driver_id": driver_id,
                "photo": photo,
                "signature_data": signature_data or "",
                "notes": notes or "",
            },
        )
        # Recargar para tener photo.name materializado en storage.
        proof.refresh_from_db()
        if not proof.photo:
            raise MissingDeliveryPhotoError("No se pudo guardar la foto de entrega")

        # Mensaje de imagen ANTES de cerrar el chat (status still open).
        chat_msg = SendOrderMessageUseCase().execute(
            order_id=order_id,
            sender_id=driver_id,
            body="Pedido entregado",
            message_type=ChatMessageType.IMAGE,
            image_name=proof.photo.name,
            allow_when_closed=False,
        )

        if order.status != OrderStatus.DELIVERED:
            order.status = OrderStatus.DELIVERED
            order.save(update_fields=["status", "updated_at"])

        broadcast_chat_closed(order_id)

        return {
            "order_id": proof.order_id,
            "photo_url": build_public_media_url(
                proof.photo.url if proof.photo else ""
            ),
            "signature_data": proof.signature_data,
            "notes": proof.notes,
            "delivered_at": proof.delivered_at,
            "chat_message_id": chat_msg.id,
            "chat_closed": True,
        }

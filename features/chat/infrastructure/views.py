from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from features.chat.application.use_cases.list_order_messages import ListOrderMessagesUseCase
from features.chat.application.use_cases.send_order_message import SendOrderMessageUseCase
from features.chat.domain.exceptions import (
    ChatClosedError,
    DomainValidationError,
    EmptyChatMessageError,
    UnauthorizedChatAccessError,
)
from features.chat.infrastructure.serializers import (
    ChatMessageSerializer,
    ChatMessagesListSerializer,
    SendChatMessageSerializer,
)
from features.orders.domain.exceptions import OrderNotFoundError


def _serialize(dto) -> dict:
    return {
        "id": dto.id,
        "order_id": dto.order_id,
        "sender_id": dto.sender_id,
        "sender_role": dto.sender_role,
        "body": dto.body,
        "message_type": dto.message_type,
        "image_url": dto.image_url,
        "created_at": dto.created_at.isoformat(),
    }


class OrderMessagesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id: int):
        try:
            result = ListOrderMessagesUseCase().execute(order_id, request.user.id)
        except OrderNotFoundError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except UnauthorizedChatAccessError as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        payload = {
            "chat_closed": result.chat_closed,
            "messages": [_serialize(m) for m in result.messages],
        }
        return Response(ChatMessagesListSerializer(payload).data)

    def post(self, request, order_id: int):
        serializer = SendChatMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            msg = SendOrderMessageUseCase().execute(
                order_id=order_id,
                sender_id=request.user.id,
                body=serializer.validated_data["body"],
            )
        except OrderNotFoundError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except (UnauthorizedChatAccessError, ChatClosedError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except (EmptyChatMessageError, DomainValidationError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            ChatMessageSerializer(_serialize(msg)).data,
            status=status.HTTP_201_CREATED,
        )

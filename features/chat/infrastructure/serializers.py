from rest_framework import serializers


class ChatMessageSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    order_id = serializers.IntegerField()
    sender_id = serializers.IntegerField()
    sender_role = serializers.CharField()
    body = serializers.CharField(allow_blank=True)
    message_type = serializers.CharField()
    image_url = serializers.CharField(allow_blank=True)
    created_at = serializers.DateTimeField()


class ChatMessagesListSerializer(serializers.Serializer):
    chat_closed = serializers.BooleanField()
    messages = ChatMessageSerializer(many=True)


class SendChatMessageSerializer(serializers.Serializer):
    body = serializers.CharField(max_length=2000, allow_blank=False)

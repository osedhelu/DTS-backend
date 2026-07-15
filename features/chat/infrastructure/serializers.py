from rest_framework import serializers


class ChatMessageSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    order_id = serializers.IntegerField()
    sender_id = serializers.IntegerField()
    sender_role = serializers.CharField()
    body = serializers.CharField()
    created_at = serializers.DateTimeField()


class SendChatMessageSerializer(serializers.Serializer):
    body = serializers.CharField(max_length=2000, allow_blank=False)

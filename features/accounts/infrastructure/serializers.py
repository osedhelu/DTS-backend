from rest_framework import serializers

from features.accounts.domain.entities import UserRole


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    role = serializers.ChoiceField(choices=[role.value for role in UserRole])
    phone = serializers.CharField(max_length=20)

    business_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    tax_id = serializers.CharField(max_length=50, required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    license_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    vehicle_type = serializers.CharField(max_length=50, required=False, allow_blank=True)
    default_address = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        role = attrs["role"]
        if role == UserRole.MERCHANT and not attrs.get("business_name"):
            raise serializers.ValidationError(
                {"business_name": "Requerido para comercios."}
            )
        return attrs


class UserResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    role = serializers.CharField()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

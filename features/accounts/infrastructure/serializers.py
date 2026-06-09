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


class DeviceTokenSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=512)
    platform = serializers.ChoiceField(
        choices=["android", "ios", "web"],
        default="android",
        required=False,
    )


class DeviceTokenResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    token = serializers.CharField()
    platform = serializers.CharField()
    is_active = serializers.BooleanField()


class MerchantRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    store_name = serializers.CharField(max_length=255)
    vertical = serializers.ChoiceField(choices=["FOOD", "SERVICES", "RETAIL"])
    category_template = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20)
    address = serializers.CharField(required=False, allow_blank=True, default="")
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)


class MerchantRegisterResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    store_id = serializers.IntegerField()
    detail = serializers.CharField()


class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.UUIDField()


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    password = serializers.CharField(min_length=8, write_only=True)

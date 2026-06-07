from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from core.openapi import DetailErrorSerializer
from core.api.throttling import ResendVerificationThrottle
from features.accounts.application.dto import RegisterMerchantWithStoreDTO, RegisterUserDTO
from features.accounts.application.use_cases.register_merchant_with_store import (
    RegisterMerchantWithStoreUseCase,
)
from features.accounts.application.use_cases.register_user import RegisterUserUseCase
from features.accounts.application.use_cases.resend_verification_email import (
    ResendVerificationEmailUseCase,
)
from features.accounts.application.use_cases.verify_email import VerifyEmailUseCase
from features.accounts.domain.entities import UserRole
from features.accounts.domain.exceptions import (
    DomainValidationError,
    DuplicateEmailError,
    EmailAlreadyVerifiedError,
    VerificationTokenAlreadyUsedError,
    VerificationTokenExpiredError,
    VerificationTokenNotFoundError,
)
from features.accounts.infrastructure.permissions import IsSuperAdmin
from features.accounts.infrastructure.repositories import DjangoUserRepository
from features.accounts.infrastructure.serializers import (
    DeviceTokenResponseSerializer,
    DeviceTokenSerializer,
    MerchantRegisterResponseSerializer,
    MerchantRegisterSerializer,
    RegisterSerializer,
    ResendVerificationSerializer,
    UserResponseSerializer,
    VerifyEmailSerializer,
)
from features.accounts.infrastructure.tasks import send_merchant_verification_email
from features.accounts.infrastructure.verification_token_repository import (
    DjangoEmailVerificationTokenRepository,
)
from features.stores.domain.entities import StoreVertical


@extend_schema_view(
    post=extend_schema(
        request=RegisterSerializer,
        responses={201: UserResponseSerializer, 400: DetailErrorSerializer},
    ),
)
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        use_case = RegisterUserUseCase(DjangoUserRepository())

        try:
            user = use_case.execute(
                RegisterUserDTO(
                    username=data["username"],
                    email=data["email"],
                    password=data["password"],
                    role=UserRole(data["role"]),
                    phone=data["phone"],
                    business_name=data.get("business_name") or None,
                    tax_id=data.get("tax_id") or None,
                    address=data.get("address") or None,
                    license_number=data.get("license_number") or None,
                    vehicle_type=data.get("vehicle_type") or None,
                    default_address=data.get("default_address") or None,
                )
            )
        except DuplicateEmailError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except DomainValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        response_serializer = UserResponseSerializer(
            {"id": user.id, "username": user.username, "email": user.email, "role": user.role}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    post=extend_schema(
        request=MerchantRegisterSerializer,
        responses={201: MerchantRegisterResponseSerializer, 400: DetailErrorSerializer},
    ),
)
class MerchantRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = MerchantRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user_repository = DjangoUserRepository()
        if user_repository.exists_by_email(data["email"]):
            return Response(
                {"detail": f"El email {data['email']} ya está registrado"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from features.stores.infrastructure.repositories import DjangoStoreRepository

        use_case = RegisterMerchantWithStoreUseCase(
            user_exists_checker=user_repository.exists_by_email,
            store_repository=DjangoStoreRepository(),
            token_repository=DjangoEmailVerificationTokenRepository(),
        )

        try:
            result = use_case.execute(
                RegisterMerchantWithStoreDTO(
                    email=data["email"],
                    password=data["password"],
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                    store_name=data["store_name"],
                    vertical=StoreVertical(data["vertical"]),
                    category_template=data["category_template"],
                    phone=data["phone"],
                    address=data.get("address") or "",
                )
            )
        except DuplicateEmailError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except DomainValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        send_merchant_verification_email.delay(result.user_id, result.verification_token)

        response_serializer = MerchantRegisterResponseSerializer(
            {
                "id": result.user_id,
                "email": result.email,
                "store_id": result.store_id,
                "detail": "Revisa tu correo para confirmar la cuenta",
            }
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    post=extend_schema(
        request=VerifyEmailSerializer,
        responses={200: DetailErrorSerializer, 400: DetailErrorSerializer},
    ),
)
class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = VerifyEmailUseCase(DjangoEmailVerificationTokenRepository())
        try:
            use_case.execute(str(serializer.validated_data["token"]))
        except VerificationTokenNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except VerificationTokenExpiredError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except VerificationTokenAlreadyUsedError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except EmailAlreadyVerifiedError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Email verificado correctamente"}, status=status.HTTP_200_OK)


@extend_schema_view(
    post=extend_schema(
        request=ResendVerificationSerializer,
        responses={200: DetailErrorSerializer, 400: DetailErrorSerializer, 429: DetailErrorSerializer},
    ),
)
class ResendVerificationView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ResendVerificationThrottle]

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = ResendVerificationEmailUseCase(DjangoEmailVerificationTokenRepository())
        try:
            result = use_case.execute(serializer.validated_data["email"])
        except EmailAlreadyVerifiedError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if result is not None:
            user, token = result
            send_merchant_verification_email.delay(user.id, token)

        return Response(
            {"detail": "Si el email está registrado, recibirás un nuevo enlace de verificación"},
            status=status.HTTP_200_OK,
        )


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["email"] = user.email
        token["user_id"] = user.id
        return token


@extend_schema_view(
    post=extend_schema(
        request=CustomTokenObtainPairSerializer,
        responses={200: CustomTokenObtainPairSerializer},
    ),
)
class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema_view(
    get=extend_schema(
        responses={
            200: inline_serializer(
                name="AdminDashboard",
                fields={
                    "detail": serializers.CharField(),
                    "user": serializers.CharField(),
                },
            ),
        },
    ),
)
class AdminDashboardView(APIView):
    """Endpoint protegido solo para Super Admin (usado en tests y web-admin)."""

    permission_classes = [IsSuperAdmin]

    def get(self, request):
        return Response({"detail": "Panel super admin", "user": request.user.username})


@extend_schema_view(
    post=extend_schema(
        request=DeviceTokenSerializer,
        responses={201: DeviceTokenResponseSerializer, 400: DetailErrorSerializer},
    ),
    delete=extend_schema(
        request=DeviceTokenSerializer,
        responses={204: None, 404: DetailErrorSerializer},
    ),
)
class DeviceTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from features.accounts.infrastructure.models import DeviceToken

        serializer = DeviceTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        device_token, _created = DeviceToken.objects.update_or_create(
            user=request.user,
            token=data["token"],
            defaults={
                "platform": data.get("platform", "android"),
                "is_active": True,
            },
        )

        return Response(
            DeviceTokenResponseSerializer(
                {
                    "id": device_token.id,
                    "token": device_token.token,
                    "platform": device_token.platform,
                    "is_active": device_token.is_active,
                }
            ).data,
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request):
        from features.accounts.infrastructure.models import DeviceToken

        serializer = DeviceTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["token"]

        deleted, _ = DeviceToken.objects.filter(user=request.user, token=token).delete()
        if deleted == 0:
            return Response(
                {"detail": "Token no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

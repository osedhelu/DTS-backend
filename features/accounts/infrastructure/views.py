from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core.openapi import DetailErrorSerializer
from core.api.throttling import PasswordResetThrottle, ResendVerificationThrottle
from features.accounts.application.dto import RegisterMerchantWithStoreDTO, RegisterUserDTO
from features.accounts.application.use_cases.confirm_password_reset import (
    ConfirmPasswordResetUseCase,
)
from features.accounts.application.use_cases.register_merchant_with_store import (
    RegisterMerchantWithStoreUseCase,
)
from features.accounts.application.use_cases.register_user import RegisterUserUseCase
from features.accounts.application.use_cases.request_password_reset import (
    RequestPasswordResetUseCase,
)
from features.accounts.application.use_cases.resend_verification_email import (
    ResendVerificationEmailUseCase,
)
from features.accounts.application.use_cases.verify_email import VerifyEmailUseCase
from features.accounts.domain.entities import UserRole
from features.accounts.domain.exceptions import (
    DomainValidationError,
    DuplicateEmailError,
    EmailAlreadyVerifiedError,
    GoogleAccountConflictError,
    InvalidGoogleTokenError,
    InvalidEarningsPeriodError,
    PasswordResetTokenAlreadyUsedError,
    PasswordResetTokenExpiredError,
    PasswordResetTokenNotFoundError,
    VerificationTokenAlreadyUsedError,
    VerificationTokenExpiredError,
    VerificationTokenNotFoundError,
)
from features.accounts.infrastructure.permissions import IsCustomer, IsDriver, IsSuperAdmin
from features.accounts.infrastructure.repositories import DjangoUserRepository
from features.accounts.infrastructure.serializers import (
    AppleAuthSerializer,
    CustomerAddressResponseSerializer,
    CustomerAddressSerializer,
    CustomerAddressUpdateSerializer,
    CustomerProfileResponseSerializer,
    CustomerProfileSerializer,
    DeviceTokenResponseSerializer,
    DeviceTokenSerializer,
    DriverAvailabilityResponseSerializer,
    DriverAvailabilitySerializer,
    DriverEarningsResponseSerializer,
    DriverProfileResponseSerializer,
    DriverProfileSerializer,
    GoogleAuthSerializer,
    MerchantRegisterResponseSerializer,
    MerchantRegisterSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    ResendVerificationSerializer,
    UserResponseSerializer,
    VerifyEmailSerializer,
)
from features.accounts.infrastructure.tasks import (
    send_merchant_verification_email,
    send_password_reset_email,
)
from features.accounts.infrastructure.password_reset_token_repository import (
    DjangoPasswordResetTokenRepository,
)
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
                    latitude=data["latitude"],
                    longitude=data["longitude"],
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


@extend_schema_view(
    post=extend_schema(
        request=PasswordResetRequestSerializer,
        responses={200: DetailErrorSerializer, 429: DetailErrorSerializer},
    ),
)
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetThrottle]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = RequestPasswordResetUseCase(DjangoPasswordResetTokenRepository())
        result = use_case.execute(serializer.validated_data["email"])

        if result.user_id is not None and result.token is not None:
            # Envío síncrono: el usuario espera el correo y en dev suele no haber worker Celery.
            send_password_reset_email(result.user_id, result.token)

        return Response({"detail": result.message}, status=status.HTTP_200_OK)


@extend_schema_view(
    post=extend_schema(
        request=PasswordResetConfirmSerializer,
        responses={200: DetailErrorSerializer, 400: DetailErrorSerializer},
    ),
)
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        use_case = ConfirmPasswordResetUseCase(DjangoPasswordResetTokenRepository())
        try:
            use_case.execute(str(data["token"]), data["password"])
        except PasswordResetTokenNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except PasswordResetTokenExpiredError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except PasswordResetTokenAlreadyUsedError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"detail": "Contraseña actualizada correctamente"},
            status=status.HTTP_200_OK,
        )


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        from features.accounts.infrastructure.jwt_tokens import (
            build_refresh_token_for_user,
        )

        return build_refresh_token_for_user(user)


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
    post=extend_schema(
        responses={200: inline_serializer(name="RefreshResponse", fields={"access": serializers.CharField()})},
    ),
)
class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]


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


@extend_schema_view(
    patch=extend_schema(
        request=DriverAvailabilitySerializer,
        responses={
            200: DriverAvailabilityResponseSerializer,
            400: DetailErrorSerializer,
            404: DetailErrorSerializer,
        },
    ),
)
class DriverAvailabilityView(APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    def patch(self, request):
        from features.accounts.application.dto import UpdateDriverAvailabilityDTO
        from features.accounts.application.use_cases.update_driver_availability import (
            UpdateDriverAvailabilityUseCase,
        )
        from features.accounts.domain.exceptions import DriverProfileNotFoundError

        serializer = DriverAvailabilitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        use_case = UpdateDriverAvailabilityUseCase()
        try:
            result = use_case.execute(
                UpdateDriverAvailabilityDTO(
                    driver_id=request.user.id,
                    is_online=data["is_online"],
                    latitude=data.get("latitude"),
                    longitude=data.get("longitude"),
                )
            )
        except DriverProfileNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            DriverAvailabilityResponseSerializer(
                {
                    "is_online": result.is_online,
                    "latitude": result.latitude,
                    "longitude": result.longitude,
                }
            ).data,
            status=status.HTTP_200_OK,
        )


def _driver_profile_response(result) -> dict:
    return {
        "full_name": result.full_name,
        "phone": result.phone,
        "license_number": result.license_number,
        "vehicle_type": result.vehicle_type,
        "vehicle_plate": result.vehicle_plate,
        "photo_url": result.photo_url,
        "onboarding_completed": result.onboarding_completed,
        "is_online": result.is_online,
        "verification_status": result.verification_status,
        "bank_name": result.bank_name,
        "bank_account_number": result.bank_account_number,
        "bank_account_type": result.bank_account_type,
    }


@extend_schema_view(
    get=extend_schema(
        responses={
            200: DriverProfileResponseSerializer,
            404: DetailErrorSerializer,
        },
    ),
    patch=extend_schema(
        request=DriverProfileSerializer,
        responses={
            200: DriverProfileResponseSerializer,
            400: DetailErrorSerializer,
            404: DetailErrorSerializer,
        },
    ),
)
class DriverProfileView(APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    def get(self, request):
        from features.accounts.application.use_cases.get_driver_profile import (
            GetDriverProfileUseCase,
        )
        from features.accounts.domain.exceptions import DriverProfileNotFoundError

        try:
            result = GetDriverProfileUseCase().execute(request.user.id)
        except DriverProfileNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            DriverProfileResponseSerializer(_driver_profile_response(result)).data,
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        from features.accounts.application.dto import UpdateDriverProfileDTO
        from features.accounts.application.use_cases.update_driver_profile import (
            UpdateDriverProfileUseCase,
        )
        from features.accounts.domain.exceptions import DriverProfileNotFoundError

        serializer = DriverProfileSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            result = UpdateDriverProfileUseCase().execute(
                UpdateDriverProfileDTO(
                    driver_id=request.user.id,
                    full_name=data.get("full_name"),
                    phone=data.get("phone"),
                    license_number=data.get("license_number"),
                    vehicle_type=data.get("vehicle_type"),
                    vehicle_plate=data.get("vehicle_plate"),
                    photo_url=data.get("photo_url"),
                    bank_name=data.get("bank_name"),
                    bank_account_number=data.get("bank_account_number"),
                    bank_account_type=data.get("bank_account_type"),
                    complete_onboarding=bool(data.get("complete_onboarding", False)),
                )
            )
        except DriverProfileNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except DomainValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            DriverProfileResponseSerializer(_driver_profile_response(result)).data,
            status=status.HTTP_200_OK,
        )


def _driver_earnings_response(result) -> dict:
    return {
        "period": result.period,
        "delivery_count": result.delivery_count,
        "total_earnings": str(result.total_earnings),
        "currency": result.currency,
        "breakdown": [
            {
                "order_id": item.order_id,
                "completed_at": item.completed_at,
                "order_total": str(item.order_total),
                "earning": str(item.earning),
            }
            for item in result.breakdown
        ],
    }


@extend_schema_view(
    get=extend_schema(
        responses={
            200: DriverEarningsResponseSerializer,
            400: DetailErrorSerializer,
        },
    ),
)
class DriverEarningsView(APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    def get(self, request):
        from features.accounts.application.use_cases.get_driver_earnings import (
            GetDriverEarningsUseCase,
        )

        period = request.query_params.get("period", "today")
        use_case = GetDriverEarningsUseCase()
        try:
            result = use_case.execute(driver_id=request.user.id, period=period)
        except InvalidEarningsPeriodError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            DriverEarningsResponseSerializer(_driver_earnings_response(result)).data,
            status=status.HTTP_200_OK,
        )


def _customer_profile_response(result) -> dict:
    return {
        "full_name": result.full_name,
        "phone": result.phone,
        "photo_url": result.photo_url,
        "default_address": result.default_address,
    }


def _customer_address_response(result) -> dict:
    return {
        "id": result.id,
        "label": result.label,
        "address": result.address,
        "latitude": result.latitude,
        "longitude": result.longitude,
        "is_default": result.is_default,
    }


@extend_schema_view(
    get=extend_schema(
        responses={
            200: CustomerProfileResponseSerializer,
            404: DetailErrorSerializer,
        },
    ),
    patch=extend_schema(
        request=CustomerProfileSerializer,
        responses={
            200: CustomerProfileResponseSerializer,
            400: DetailErrorSerializer,
            404: DetailErrorSerializer,
        },
    ),
)
class CustomerProfileView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def get(self, request):
        from features.accounts.application.use_cases.get_customer_profile import (
            GetCustomerProfileUseCase,
        )
        from features.accounts.domain.exceptions import CustomerProfileNotFoundError

        try:
            result = GetCustomerProfileUseCase().execute(request.user.id)
        except CustomerProfileNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            CustomerProfileResponseSerializer(_customer_profile_response(result)).data,
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        from features.accounts.application.dto import UpdateCustomerProfileDTO
        from features.accounts.application.use_cases.update_customer_profile import (
            UpdateCustomerProfileUseCase,
        )
        from features.accounts.domain.exceptions import CustomerProfileNotFoundError

        serializer = CustomerProfileSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            result = UpdateCustomerProfileUseCase().execute(
                UpdateCustomerProfileDTO(
                    customer_id=request.user.id,
                    full_name=data.get("full_name"),
                    phone=data.get("phone"),
                    photo_url=data.get("photo_url"),
                    default_address=data.get("default_address"),
                )
            )
        except CustomerProfileNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except DomainValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            CustomerProfileResponseSerializer(_customer_profile_response(result)).data,
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    get=extend_schema(
        responses={200: CustomerAddressResponseSerializer(many=True)},
    ),
    post=extend_schema(
        request=CustomerAddressSerializer,
        responses={
            201: CustomerAddressResponseSerializer,
            400: DetailErrorSerializer,
        },
    ),
)
class CustomerAddressListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def get(self, request):
        from features.accounts.application.use_cases.list_customer_addresses import (
            ListCustomerAddressesUseCase,
        )

        results = ListCustomerAddressesUseCase().execute(request.user.id)
        return Response(
            CustomerAddressResponseSerializer(
                [_customer_address_response(item) for item in results],
                many=True,
            ).data,
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        from features.accounts.application.dto import CreateCustomerAddressDTO
        from features.accounts.application.use_cases.create_customer_address import (
            CreateCustomerAddressUseCase,
        )

        serializer = CustomerAddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        result = CreateCustomerAddressUseCase().execute(
            CreateCustomerAddressDTO(
                customer_id=request.user.id,
                label=data["label"],
                address=data["address"],
                latitude=data["latitude"],
                longitude=data["longitude"],
                is_default=data.get("is_default", False),
            )
        )

        return Response(
            CustomerAddressResponseSerializer(_customer_address_response(result)).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    patch=extend_schema(
        request=CustomerAddressUpdateSerializer,
        responses={
            200: CustomerAddressResponseSerializer,
            400: DetailErrorSerializer,
            404: DetailErrorSerializer,
        },
    ),
    delete=extend_schema(
        responses={
            204: None,
            404: DetailErrorSerializer,
        },
    ),
)
class CustomerAddressDetailView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def patch(self, request, address_id: int):
        from features.accounts.application.dto import UpdateCustomerAddressDTO
        from features.accounts.application.use_cases.update_customer_address import (
            UpdateCustomerAddressUseCase,
        )
        from features.accounts.domain.exceptions import CustomerAddressNotFoundError

        serializer = CustomerAddressUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            result = UpdateCustomerAddressUseCase().execute(
                UpdateCustomerAddressDTO(
                    customer_id=request.user.id,
                    address_id=address_id,
                    label=data.get("label"),
                    address=data.get("address"),
                    latitude=data.get("latitude"),
                    longitude=data.get("longitude"),
                    is_default=data.get("is_default"),
                )
            )
        except CustomerAddressNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            CustomerAddressResponseSerializer(_customer_address_response(result)).data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, address_id: int):
        from features.accounts.application.use_cases.delete_customer_address import (
            DeleteCustomerAddressUseCase,
        )
        from features.accounts.domain.exceptions import CustomerAddressNotFoundError

        try:
            DeleteCustomerAddressUseCase().execute(request.user.id, address_id)
        except CustomerAddressNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    post=extend_schema(
        request=GoogleAuthSerializer,
        responses={
            200: inline_serializer(
                name="GoogleAuthResponse",
                fields={
                    "access": serializers.CharField(),
                    "refresh": serializers.CharField(),
                },
            ),
            400: DetailErrorSerializer,
            401: DetailErrorSerializer,
        },
    ),
)
class GoogleAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from features.accounts.application.use_cases.google_sign_in import (
            GoogleSignInUseCase,
        )
        from features.notifications.domain.exceptions import FCMNotConfiguredError

        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = GoogleSignInUseCase()
        try:
            tokens = use_case.execute(
                serializer.validated_data["id_token"],
                role=serializer.validated_data.get("role") or UserRole.CUSTOMER,
            )
        except InvalidGoogleTokenError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)
        except GoogleAccountConflictError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except FCMNotConfiguredError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(tokens, status=status.HTTP_200_OK)


@extend_schema(
    request=AppleAuthSerializer,
    responses={
        200: inline_serializer(
            name="AppleAuthResponse",
            fields={
                "access": serializers.CharField(),
                "refresh": serializers.CharField(),
            },
        ),
        400: DetailErrorSerializer,
        401: DetailErrorSerializer,
    },
)
class AppleAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from features.accounts.application.use_cases.apple_sign_in import (
            AppleSignInUseCase,
        )
        from features.notifications.domain.exceptions import FCMNotConfiguredError

        serializer = AppleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = AppleSignInUseCase()
        data = serializer.validated_data
        email = (data.get("email") or "").strip() or None
        full_name = (data.get("full_name") or "").strip() or None
        try:
            tokens = use_case.execute(
                data["id_token"],
                role=data.get("role") or UserRole.CUSTOMER,
                email=email,
                full_name=full_name,
            )
        except InvalidGoogleTokenError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)
        except GoogleAccountConflictError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except FCMNotConfiguredError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(tokens, status=status.HTTP_200_OK)

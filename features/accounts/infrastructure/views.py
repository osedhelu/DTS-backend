from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from features.accounts.application.dto import RegisterUserDTO
from features.accounts.application.use_cases.register_user import RegisterUserUseCase
from features.accounts.domain.entities import UserRole
from features.accounts.domain.exceptions import DomainValidationError, DuplicateEmailError
from features.accounts.infrastructure.repositories import DjangoUserRepository
from features.accounts.infrastructure.serializers import RegisterSerializer, UserResponseSerializer


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


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["email"] = user.email
        return token


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer

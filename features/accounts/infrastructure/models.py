from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

from features.accounts.domain.entities import UserRole
from features.stores.domain.value_objects import GeoLocation


class CustomUserManager(BaseUserManager):
    def create_user(
        self,
        username: str,
        email: str,
        password: str | None = None,
        role: str = UserRole.CUSTOMER,
        **extra_fields,
    ):
        if not email:
            raise ValueError("El email es obligatorio")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        username: str,
        email: str,
        password: str | None = None,
        **extra_fields,
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", UserRole.SUPER_ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser debe tener is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser debe tener is_superuser=True")

        return self.create_user(username, email, password, **extra_fields)


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=[(role.value, role.value) for role in UserRole],
        default=UserRole.CUSTOMER,
    )

    objects = CustomUserManager()

    REQUIRED_FIELDS = ["email"]

    class Meta:
        db_table = "accounts_user"
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self) -> str:
        return f"{self.username} ({self.role})"

    @property
    def is_merchant(self) -> bool:
        return self.role == UserRole.MERCHANT

    @property
    def is_driver(self) -> bool:
        return self.role == UserRole.DRIVER

    @property
    def is_customer(self) -> bool:
        return self.role == UserRole.CUSTOMER

    @property
    def is_super_admin(self) -> bool:
        return self.role == UserRole.SUPER_ADMIN


class MerchantProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="merchant_profile",
    )
    business_name = models.CharField(max_length=255)
    tax_id = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_merchant_profile"
        verbose_name = "perfil comercio"
        verbose_name_plural = "perfiles comercio"

    def __str__(self) -> str:
        return self.business_name


class DriverProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="driver_profile",
    )
    phone = models.CharField(max_length=20)
    license_number = models.CharField(max_length=50, blank=True)
    vehicle_type = models.CharField(max_length=50, blank=True)
    is_online = models.BooleanField(default=False)
    last_latitude = models.FloatField(null=True, blank=True)
    last_longitude = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_driver_profile"
        verbose_name = "perfil conductor"
        verbose_name_plural = "perfiles conductor"

    def __str__(self) -> str:
        return f"Conductor {self.user.username}"

    def set_last_location(self, geo: GeoLocation) -> None:
        self.last_latitude = geo.latitude
        self.last_longitude = geo.longitude

    @property
    def has_last_location(self) -> bool:
        return self.last_latitude is not None and self.last_longitude is not None


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="customer_profile",
    )
    phone = models.CharField(max_length=20)
    default_address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_customer_profile"
        verbose_name = "perfil cliente"
        verbose_name_plural = "perfiles cliente"

    def __str__(self) -> str:
        return f"Cliente {self.user.username}"


class DevicePlatform(models.TextChoices):
    ANDROID = "android", "Android"
    IOS = "ios", "iOS"
    WEB = "web", "Web"


class DeviceToken(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="device_tokens",
    )
    token = models.CharField(max_length=512)
    platform = models.CharField(
        max_length=10,
        choices=DevicePlatform.choices,
        default=DevicePlatform.ANDROID,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_device_token"
        verbose_name = "token de dispositivo"
        verbose_name_plural = "tokens de dispositivo"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "token"],
                name="unique_device_token_per_user",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} — {self.platform}"

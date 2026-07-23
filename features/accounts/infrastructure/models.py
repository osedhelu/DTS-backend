import uuid

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
    email_verified = models.BooleanField(default=False)
    google_uid = models.CharField(max_length=128, unique=True, null=True, blank=True)
    apple_uid = models.CharField(max_length=128, unique=True, null=True, blank=True)
    auth_provider = models.CharField(
        max_length=20,
        choices=[
            ("local", "local"),
            ("google", "google"),
            ("apple", "apple"),
        ],
        default="local",
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
    full_name = models.CharField(max_length=150, blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    vehicle_type = models.CharField(max_length=50, blank=True)
    vehicle_plate = models.CharField(max_length=20, blank=True)
    photo_url = models.URLField(blank=True)
    id_document_url = models.URLField(blank=True, default="")
    verification_status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "pending"),
            ("approved", "approved"),
            ("rejected", "rejected"),
        ],
        default="pending",
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    bank_name = models.CharField(max_length=100, blank=True, default="")
    bank_account_number = models.CharField(max_length=50, blank=True, default="")
    bank_account_type = models.CharField(max_length=30, blank=True, default="")
    onboarding_completed_at = models.DateTimeField(null=True, blank=True)
    is_online = models.BooleanField(default=False)
    last_latitude = models.FloatField(null=True, blank=True)
    last_longitude = models.FloatField(null=True, blank=True)
    work_center_latitude = models.FloatField(null=True, blank=True)
    work_center_longitude = models.FloatField(null=True, blank=True)
    work_radius_km = models.FloatField(default=5.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def onboarding_completed(self) -> bool:
        return self.onboarding_completed_at is not None

    @property
    def has_work_center(self) -> bool:
        return (
            self.work_center_latitude is not None
            and self.work_center_longitude is not None
        )

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
    full_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=20)
    photo_url = models.URLField(blank=True)
    default_address = models.TextField(blank=True)
    search_center_latitude = models.FloatField(null=True, blank=True)
    search_center_longitude = models.FloatField(null=True, blank=True)
    search_radius_km = models.FloatField(default=5.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def has_search_center(self) -> bool:
        return (
            self.search_center_latitude is not None
            and self.search_center_longitude is not None
        )

    class Meta:
        db_table = "accounts_customer_profile"
        verbose_name = "perfil cliente"
        verbose_name_plural = "perfiles cliente"

    def __str__(self) -> str:
        return f"Cliente {self.user.username}"

    def display_full_name(self) -> str:
        name = (self.full_name or "").strip()
        if name:
            return name
        user_name = self.user.get_full_name().strip()
        if user_name:
            return user_name
        return self.user.username


class CustomerAddress(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="customer_addresses",
    )
    label = models.CharField(max_length=100)
    address = models.TextField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_customer_address"
        verbose_name = "dirección cliente"
        verbose_name_plural = "direcciones cliente"
        ordering = ["-is_default", "-updated_at"]

    def __str__(self) -> str:
        return f"{self.label} — {self.user.username}"


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


class EmailVerificationToken(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="verification_tokens",
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "accounts_email_verification_token"
        verbose_name = "token de verificación email"
        verbose_name_plural = "tokens de verificación email"

    def __str__(self) -> str:
        return f"Token {self.token} — {self.user.email}"


class PasswordResetToken(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "accounts_password_reset_token"
        verbose_name = "token de recuperación de contraseña"
        verbose_name_plural = "tokens de recuperación de contraseña"

    def __str__(self) -> str:
        return f"Reset {self.token} — {self.user.email}"


class DriverPayoutRequest(models.Model):
    driver = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="payout_requests",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "pending"),
            ("paid", "paid"),
            ("rejected", "rejected"),
        ],
        default="pending",
    )
    notes = models.TextField(blank=True, default="")
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "accounts_driver_payout_request"
        verbose_name = "solicitud de retiro"
        verbose_name_plural = "solicitudes de retiro"
        ordering = ["-requested_at"]


class FavoriteStore(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="favorite_stores",
    )
    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.CASCADE,
        related_name="favorited_by",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "accounts_favorite_store"
        verbose_name = "tienda favorita"
        verbose_name_plural = "tiendas favoritas"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "store"],
                name="unique_favorite_store_per_user",
            ),
        ]

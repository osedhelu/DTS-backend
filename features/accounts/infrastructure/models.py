from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

from features.accounts.domain.entities import UserRole


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

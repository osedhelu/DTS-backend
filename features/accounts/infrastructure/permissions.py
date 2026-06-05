from rest_framework.permissions import BasePermission

from features.accounts.domain.entities import UserRole


class _RolePermission(BasePermission):
    allowed_roles: tuple[str, ...] = ()

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.role in self.allowed_roles


class IsSuperAdmin(_RolePermission):
    allowed_roles = (UserRole.SUPER_ADMIN,)


class IsMerchant(_RolePermission):
    allowed_roles = (UserRole.MERCHANT,)


class IsDriver(_RolePermission):
    allowed_roles = (UserRole.DRIVER,)


class IsCustomer(_RolePermission):
    allowed_roles = (UserRole.CUSTOMER,)

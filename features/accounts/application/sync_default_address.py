from features.accounts.infrastructure.models import CustomerAddress, CustomerProfile


def sync_profile_default_address(customer_id: int) -> None:
    """Keep CustomerProfile.default_address aligned with CustomerAddress.is_default."""
    try:
        profile = CustomerProfile.objects.get(user_id=customer_id)
    except CustomerProfile.DoesNotExist:
        return

    default = (
        CustomerAddress.objects.filter(user_id=customer_id, is_default=True)
        .order_by("-updated_at")
        .first()
    )
    if default is None:
        default = (
            CustomerAddress.objects.filter(user_id=customer_id)
            .order_by("-updated_at")
            .first()
        )
        if default is not None:
            CustomerAddress.objects.filter(id=default.id).update(is_default=True)

    new_value = default.address if default is not None else ""
    if profile.default_address != new_value:
        profile.default_address = new_value
        profile.save(update_fields=["default_address", "updated_at"])

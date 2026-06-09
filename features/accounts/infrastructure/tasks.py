from celery import shared_task

from features.accounts.application.use_cases.send_merchant_verification_email import (
    SendMerchantVerificationEmailUseCase,
)
from features.accounts.application.use_cases.send_password_reset_email import (
    SendPasswordResetEmailUseCase,
)
from features.accounts.infrastructure.models import CustomUser, MerchantProfile


@shared_task(
    bind=True,
    max_retries=3,
    name="features.accounts.infrastructure.tasks.send_merchant_verification_email",
)
def send_merchant_verification_email(self, user_id: int, token: str) -> str:
    user = CustomUser.objects.get(pk=user_id)
    profile = MerchantProfile.objects.filter(user=user).first()
    store_name = profile.business_name if profile else user.username
    use_case = SendMerchantVerificationEmailUseCase()
    return use_case.execute(email=user.email, token=token, store_name=store_name)


@shared_task(
    bind=True,
    max_retries=3,
    name="features.accounts.infrastructure.tasks.send_password_reset_email",
)
def send_password_reset_email(self, user_id: int, token: str) -> str:
    user = CustomUser.objects.get(pk=user_id)
    use_case = SendPasswordResetEmailUseCase()
    return use_case.execute(email=user.email, token=token, username=user.username)

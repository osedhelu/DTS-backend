import logging
import smtplib

from celery import shared_task
from django.core.mail import get_connection

from features.accounts.application.use_cases.send_merchant_verification_email import (
    SendMerchantVerificationEmailUseCase,
)
from features.accounts.application.use_cases.send_password_reset_email import (
    SendPasswordResetEmailUseCase,
)
from features.accounts.infrastructure.models import CustomUser, MerchantProfile

logger = logging.getLogger(__name__)

_RETRYABLE_EMAIL_ERRORS = (
    OSError,
    smtplib.SMTPException,
    ConnectionError,
    TimeoutError,
)


@shared_task(
    bind=True,
    max_retries=3,
    name="features.accounts.infrastructure.tasks.send_merchant_verification_email",
)
def send_merchant_verification_email(self, user_id: int, token: str) -> str:
    try:
        user = CustomUser.objects.get(pk=user_id)
        profile = MerchantProfile.objects.filter(user=user).first()
        store_name = profile.business_name if profile else user.username
        use_case = SendMerchantVerificationEmailUseCase()
        result = use_case.execute(email=user.email, token=token, store_name=store_name)
        logger.info(
            "merchant_verification_email_sent user_id=%s email=%s backend=%s",
            user_id,
            user.email,
            get_connection().__class__.__name__,
        )
        return result
    except CustomUser.DoesNotExist:
        logger.exception("merchant_verification_email_user_missing user_id=%s", user_id)
        raise
    except _RETRYABLE_EMAIL_ERRORS as exc:
        logger.warning(
            "merchant_verification_email_retry user_id=%s attempt=%s error=%s",
            user_id,
            self.request.retries,
            exc,
        )
        raise self.retry(exc=exc, countdown=2**self.request.retries) from exc


@shared_task(
    bind=True,
    max_retries=3,
    name="features.accounts.infrastructure.tasks.send_password_reset_email",
)
def send_password_reset_email(self, user_id: int, token: str) -> str:
    try:
        user = CustomUser.objects.get(pk=user_id)
        use_case = SendPasswordResetEmailUseCase()
        result = use_case.execute(email=user.email, token=token, username=user.username)
        logger.info(
            "password_reset_email_sent user_id=%s email=%s backend=%s",
            user_id,
            user.email,
            get_connection().__class__.__name__,
        )
        return result
    except CustomUser.DoesNotExist:
        logger.exception("password_reset_email_user_missing user_id=%s", user_id)
        raise
    except _RETRYABLE_EMAIL_ERRORS as exc:
        logger.warning(
            "password_reset_email_retry user_id=%s attempt=%s error=%s",
            user_id,
            self.request.retries,
            exc,
        )
        raise self.retry(exc=exc, countdown=2**self.request.retries) from exc

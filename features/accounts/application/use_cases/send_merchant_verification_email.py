from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

EMAIL_TEMPLATE_TEXT = "notifications/merchant_verification_email.txt"
EMAIL_TEMPLATE_HTML = "notifications/merchant_verification_email.html"


class SendMerchantVerificationEmailUseCase:
    def execute(self, email: str, token: str, store_name: str) -> str:
        web_url = getattr(settings, "WEB_URL", "http://localhost:3000")
        verify_url = f"{web_url}/confirmar-email?token={token}"
        context = {
            "store_name": store_name,
            "verify_url": verify_url,
        }

        text_body = render_to_string(EMAIL_TEMPLATE_TEXT, context)
        html_body = render_to_string(EMAIL_TEMPLATE_HTML, context)
        subject = "Confirma tu correo — DTS Delivery"

        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        message.attach_alternative(html_body, "text/html")
        message.send()

        return f"sent:{email}"

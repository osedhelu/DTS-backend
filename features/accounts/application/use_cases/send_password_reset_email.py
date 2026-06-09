from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

EMAIL_TEMPLATE_TEXT = "notifications/password_reset_email.txt"
EMAIL_TEMPLATE_HTML = "notifications/password_reset_email.html"


class SendPasswordResetEmailUseCase:
    def execute(self, email: str, token: str, username: str) -> str:
        web_url = getattr(settings, "WEB_URL", "http://localhost:3000")
        reset_url = f"{web_url}/restablecer-contrasena?token={token}"
        context = {
            "username": username,
            "reset_url": reset_url,
        }

        text_body = render_to_string(EMAIL_TEMPLATE_TEXT, context)
        html_body = render_to_string(EMAIL_TEMPLATE_HTML, context)
        subject = "Recupera tu contraseña — DTS Delivery"

        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        message.attach_alternative(html_body, "text/html")
        message.send()

        return f"sent:{email}"

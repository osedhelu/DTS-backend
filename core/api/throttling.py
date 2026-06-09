from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class AnonBurstThrottle(AnonRateThrottle):
    scope = "anon"


class UserBurstThrottle(UserRateThrottle):
    scope = "user"


class ResendVerificationThrottle(AnonRateThrottle):
    scope = "resend_verification"


class PasswordResetThrottle(AnonRateThrottle):
    scope = "password_reset"

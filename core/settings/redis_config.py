"""Configuración Redis — T1.1.2."""


def build_redis_url(env) -> str:
    return env("REDIS_URL", default="redis://localhost:6379/0")

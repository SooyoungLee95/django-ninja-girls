from types import SimpleNamespace

from .base import *  # noqa: F403

ALLOWED_HOSTS += ["host.docker.internal"]  # noqa: F405

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("DJANGO_SECRET_KEY")  # noqa: F405

AUTHYO = SimpleNamespace(
    BASE_URL=env.str("AUTHYO_URL", default="https://staging-authyo.yogiyo.co.kr/"),  # noqa: F405
    AUTHORIZATION_CODE_FERNET_KEY=env.str(  # noqa: F405
        "FERNET_CRYPTO_KEY", default="CkjxwCCPDYkrS0d6-bmhDsuIcnajgutUDkqeZE-PkSw="
    ).encode(),
)

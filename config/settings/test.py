from types import SimpleNamespace

from .base import *  # noqa: F401,F403

SECRET_KEY = "GFog0tYABTssUAuZyvh0os6nCxyfJeVWyXFXv5nrZid3AmbEZpDFxQo5998UWTMm"  # mock SECRET_KEY for passing test

AUTHYO = SimpleNamespace(
    BASE_URL=env.str("AUTHYO_URL", default="https://staging-authyo.yogiyo.co.kr/"),  # noqa: F405
    AUTHORIZATION_CODE_FERNET_KEY=env.str(  # noqa: F405
        "FERNET_CRYPTO_KEY", default="CkjxwCCPDYkrS0d6-bmhDsuIcnajgutUDkqeZE-PkSw="
    ).encode(),
)

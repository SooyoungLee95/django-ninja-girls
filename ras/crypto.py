from cryptography.fernet import Fernet
from django.conf import settings

frt = Fernet(settings.FERNET_CRYPTO_KEY)


def encrypt(value):
    return frt.encrypt(str(value).encode()).decode()


def decrypt(value):
    return frt.decrypt(value.encode()).decode()

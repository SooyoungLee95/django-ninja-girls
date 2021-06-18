from .base import *  # noqa: F403

ALLOWED_HOSTS += ["host.docker.internal"]  # noqa: F405

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("DJANGO_SECRET_KEY")  # noqa: F405

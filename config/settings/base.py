"""
Django settings for ras project.

Generated by 'django-admin startproject' using Django 3.2.2.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
from pathlib import Path

import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
env.read_env(str(BASE_DIR / ".env"))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1"]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "ras.rideryo.apps.RideryoConfig",
    "ras.simulator.apps.SimulatorConfig",
    "ras.rider_app.apps.RiderAppConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
}

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "ko"

TIME_ZONE = "Asia/Seoul"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = "/static/"

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# AWS
AWS_ACCESS_KEY_ID = env.str("AWS_ACCESS_KEY_ID", default="test")
AWS_SECRET_ACCESS_KEY = env.str("AWS_SECRET_ACCESS_KEY", default="test")
AWS_REGION = env.str("AWS_REGION", default="us-east-1")
AWS_SNS_ENDPOINT_URL = env.str("AWS_SNS_ENDPOINT_URL", default="http://0.0.0.0:4566")


# Jungleworks
JUNGLEWORKS_BASE_URL = env.str("JUNGLEWORKS_BASE_URL", default="https://api.tookanapp.com")
JUNGLEWORKS_API_KEY = env.str("JUNGLEWORKS_API_KEY", default="")
JUNGLEWORKS_ENABLE = env.bool("JUNGLEWORKS_ENABLE", default=False)


# 개인정보 암호화/복호화 키
FERNET_CRYPTO_KEY = env.str("FERNET_CRYPTO_KEY", default="CkjxwCCPDYkrS0d6-bmhDsuIcnajgutUDkqeZE-PkSw=").encode()


# FCM Credentials
FCM_SERVICE_ACCOUNT_KEY_FILENAME = env.str("FCM_SERVICE_ACCOUNT_KEY_FILENAME", default="serviceAccountKey.json")

# AUTHYO JWT payload 암호화/복호화 키
AUTHYO_FERNET_CRYPTO_KEY = env.str(
    "AUTHYO_FERNET_CRYPTO_KEY", default="CkjxwCCPDYkrS0d6-bmhDsuIcnajgutUDkqeZE-PkSw="
).encode()

# Rideryo
RIDERYO_BASE_URL = env.str("RIDERYO_BASE_URL", default="http://rideryo-dev")
RIDERYO_ENV = env.str("RIDERYO_BASE_URL", default="rideryo-dev")

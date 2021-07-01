from django.conf import settings

AUTHYO_LOGIN_URL = f"{settings.AUTHYO.BASE_URL}/api/v1/auth/authorize"

RIDER_APP_INITIAL_PASSWORD = "TestTest"

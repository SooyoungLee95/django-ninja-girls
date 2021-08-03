from .base import *  # noqa: F405,F401,F403

SECRET_KEY = "GFog0tYABTssUAuZyvh0os6nCxyfJeVWyXFXv5nrZid3AmbEZpDFxQo5998UWTMm"  # mock SECRET_KEY for passing test


AUTHYO = SimpleNamespace(  # noqa: F405
    BASE_URL="https://staging-authyo.yogiyo.co.kr",
    FERNET_CRYPTO_KEY="azFuf3CpHYihwAUs5Cf0-_S3QJVfi-ZbS9rkJtIdkHI=".encode(),
    SECRET_KEY="""-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCJcExoaKfVlIBH6q2IyFbPOCRS
5+JfIQWDou3wQ2JadCkglsc83g0rc0Yvk8Z9sbFdsi3wnL3dO+3/yklpNO19qICe
8ga4bAry70xQNCzxw2GZ8+6jNFB8vhZ7q24rd27GCP+IKX/sSvi6YU6zkv9UJno9
M4ER4mAIz2cETX7rbQIDAQAB
-----END PUBLIC KEY-----""",
    ALGORITHM="RS256",
)

HUBYO_CONFIG = HubyoConfig(  # noqa: F405
    SNS_TOPIC_ARN=HubyoConfig.SNSTopicEnv.DEV,  # noqa: F405
    PLATFORM=HubyoConfig.Platform.YGY_STAGING_G,  # noqa: F405
    PUBLISHER=HubyoConfig.Publisher.ETC,  # noqa: F405
    AWS_ACCESS_KEY=env.str("HUBYO_AWS_ACCESS_KEY", default="test"),  # noqa: F405
    AWS_SECRET_ACCESS_KEY=env.str("HUBYO_AWS_SECRET_ACCESS_KEY", default="test"),  # noqa: F405
    AWS_REGION_NAME=env.str("HUBYO_AWS_REGION_NAME", default="ap-northeast-2"),  # noqa: F405
)

from enum import Enum


class WebhookName(str, Enum):
    AUTO_ALLOCATION_SUCCESS = "auto_allocation_success"
    MOCK_AUTO_ALLOCATION_SUCCESS = "task_update"

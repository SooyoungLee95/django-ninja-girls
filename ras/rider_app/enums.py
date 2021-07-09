from enum import Enum


class WebhookName(str, Enum):
    AUTO_ALLOCATION_SUCCESS = "auto_allocation_success"
    MOCK_AUTO_ALLOCATION_SUCCESS = "task_update"


class PushAction(str, Enum):
    NEAR_PICKUP = "dispatch-request:near-pickup"
    NEAR_DROPOFF = "dispatch-request:near-dropoff"
    DISPATCHED = "dispatch-request:dispatched"
    BAN = "dispatch-request:ban"
    UNDO_BAN = "dispatch-request:undo-ban"

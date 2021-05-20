from ninja import Router

from .views import trigger_router

router = Router()
router.add_router("triggers", trigger_router, tags=["Simulator Triggers"])

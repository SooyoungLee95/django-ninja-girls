from ninja import Router

from .views import rider_router

router = Router()
router.add_router("rider", rider_router, tags=["RiderApp Rider"])

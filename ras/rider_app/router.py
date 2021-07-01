from ninja import Router

from .views import auth_router, rider_router

router = Router()
router.add_router("rider", rider_router, tags=["RiderApp Rider"])
router.add_router("account", auth_router, tags=["RiderApp Auth"])

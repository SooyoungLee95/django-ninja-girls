from ninja import Router

from .views import auth_router, dispatch_request_router, rider_router, sns_router

router = Router()
router.add_router("rider", rider_router, tags=["RiderApp Rider"])
router.add_router("account", auth_router, tags=["RiderApp Auth"])
router.add_router("dispatch-request", dispatch_request_router, tags=["RiderApp Dispatch Request"])
router.add_router("sns", sns_router, tags=["RiderApp SNS Notification"])

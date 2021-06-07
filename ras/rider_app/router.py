from ninja import Router

from .views import jungleworks_rider_router, rider_router

router = Router()
jw_router = Router()

router.add_router("rider", rider_router, tags=["RiderApp Rider"])
jw_router.add_router("rider", jungleworks_rider_router, tags=["RiderApp Rider", "Jungleworks"])

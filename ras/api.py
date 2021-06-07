from django.conf import settings
from ninja import NinjaAPI

from ras.rider_app.router import jw_router as jw_rider_app_router
from ras.rider_app.router import router as rider_app_router
from ras.simulator.router import router as simulator_router

api = NinjaAPI(
    title="Rider API Service",
    description="Rider와 Shift를 관리하는 API 서비스",
    version="0.0.1",
)

if settings.JUNGLEWORKS_ENABLE:
    api.add_router("rider-app", jw_rider_app_router)
else:
    api.add_router("rider-app", rider_app_router)

api.add_router("simulator", simulator_router)

if settings.DEBUG:
    api.add_router("jw/rider-app", jw_rider_app_router)

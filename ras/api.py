from ninja import NinjaAPI
from ninja.errors import ValidationError

from ras.helpers import validation_error_handler
from ras.rider_app.router import router as rider_app_router
from ras.rider_app.views import mock_authyo_router
from ras.simulator.router import router as simulator_router

api = NinjaAPI(
    title="Rider API Service",
    description="Rider와 Shift를 관리하는 API 서비스",
    version="0.0.1",
)
api.add_exception_handler(ValidationError, validation_error_handler)

api.add_router("rider-app", rider_app_router)
api.add_router("simulator", simulator_router)

api.add_router("mock_authyo", mock_authyo_router, tags=["Mock Authyo"])

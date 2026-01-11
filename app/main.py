# app/main.py
import asyncio
import logging
from fastapi import FastAPI

from app.core.config import AppConfig
from app.core.logging_config import configure_logging
from app.database.database import Database
from app.api.routers.health_router import router as health_router
from app.api.routers.status_router import router as status_router
from app.api.routers.setup_router import router as setup_router
from app.api.routers.sensors_router import router as sensors_router
from app.api.routers.curves_router import router as curves_router
from app.api.routers.settings_router import router as settings_router
from app.api.routers.control_router import router as control_router
from app.services.control_loop_service import ControlLoopService


logger = logging.getLogger(__name__)

app = FastAPI(title="Raspberry Pi Fan PWM Backend", version="1.0.0")

_config = AppConfig.from_env()
configure_logging(_config.log_level)

_db = Database(_config.data_dir)
_control_loop: ControlLoopService | None = None
_control_task: asyncio.Task | None = None


@app.on_event("startup")
async def on_startup() -> None:
    global _control_loop, _control_task
    _db.init()
    _control_loop = ControlLoopService(db=_db, config=_config)
    _control_task = asyncio.create_task(_control_loop.run())
    logger.info("Startup complete")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    global _control_loop, _control_task
    if _control_loop is not None:
        _control_loop.stop()
    if _control_task is not None:
        try:
            await asyncio.wait_for(_control_task, timeout=5)
        except Exception:
            pass
    logger.info("Shutdown complete")


app.include_router(health_router)
app.include_router(status_router)
app.include_router(setup_router)
app.include_router(sensors_router)
app.include_router(curves_router)
app.include_router(settings_router)
app.include_router(control_router)
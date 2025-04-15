import uvicorn
import logging
from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.responses import RedirectResponse

from app.api.api import api_router
from app.settings import settings
from app.db.database import Database
from app.tasks.background_refresh import background_refresh_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.RATE_LIMITING_FREQUENCY],
    enabled=settings.RATE_LIMITING_ENABLE,
)
app = FastAPI(title="Transfermarkt API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.include_router(api_router)


@app.get("/", include_in_schema=False)
def docs_redirect():
    return RedirectResponse(url="/docs")


@app.on_event("startup")
async def startup_db_client():
    # Connect to MongoDB
    await Database.connect_to_mongodb()
    
    # Start the background refresh service
    # await background_refresh_service.start()
    # logger.info("Background refresh service temporarily disabled for debugging.")


@app.on_event("shutdown")
async def shutdown_db_client():
    # Stop the background refresh service
    await background_refresh_service.stop()
    
    # Close MongoDB connection
    await Database.close_mongodb_connection()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

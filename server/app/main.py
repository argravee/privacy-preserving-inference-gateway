from fastapi import FastAPI

from server.app.routes.health import router as health_router
from server.app.routes.infer import router as infer_router
from server.app.routes.jobs import router as jobs_router
from server.app.routes.models import router as models_router
from server.app.routes.infer_plain import router as infer_plain_router

app = FastAPI(title="Encrypted Inference API")

app.include_router(health_router)
app.include_router(models_router)
app.include_router(infer_router)
app.include_router(jobs_router)
app.include_router(infer_plain_router)
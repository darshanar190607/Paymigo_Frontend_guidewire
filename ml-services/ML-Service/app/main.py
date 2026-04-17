from fastapi import FastAPI
from app.api import cluster, premium, trigger, curfew, fraud, forecast, health, payout_manager, testing_framework, geotruth
from app.pipelines import weather_orchestrator

app = FastAPI(title="ML Service", version="1.0.0")

@app.get("/")
def read_root():
    return {"status": "online", "message": "PayMigo ML Service is running", "documentation": "/docs"}

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(cluster.router, prefix="/cluster", tags=["cluster"])
app.include_router(premium.router, prefix="/premium", tags=["premium"])
app.include_router(trigger.router, prefix="/trigger", tags=["trigger"])
app.include_router(curfew.router, prefix="/curfew", tags=["curfew"])
app.include_router(fraud.router, prefix="/fraud", tags=["fraud"])
app.include_router(forecast.router, prefix="/forecast", tags=["forecast"])
app.include_router(geotruth.router, prefix="/geotruth", tags=["geotruth"])
app.include_router(weather_orchestrator.router, prefix="/orchestrator/pipeline", tags=["orchestrator"])
app.include_router(payout_manager.router, prefix="/orchestrator/pipeline/payout", tags=["payout_manager"])
app.include_router(testing_framework.router, prefix="/orchestrator/testing", tags=["testing"])

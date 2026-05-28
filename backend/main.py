from fastapi import FastAPI

from backend.database import Base, engine
from backend.routers import jobs, agent

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Recon Dataset Inspector Backend",
    description="三维重建数据处理与智能诊断后端系统",
    version="0.1.0"
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Recon Dataset Inspector Backend is running."
    }


app.include_router(jobs.router)
app.include_router(agent.router)

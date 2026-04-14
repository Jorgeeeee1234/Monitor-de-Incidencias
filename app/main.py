from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.api.controllers.session_controller import router as session_router
from app.api.controllers.message_controller import router as message_router
from app.api.controllers.incident_controller import router as incident_router
from app.api.controllers.dashboard_controller import router as dashboard_router
from app.api.controllers.viewbd_controller import router as viewbd_router
from app.api.controllers.prompt_check_controller import router as prompt_check_router

app = FastAPI(title="Security Incident Registry")

Base.metadata.create_all(bind=engine)

app.include_router(session_router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(message_router, prefix="/api/messages", tags=["Messages"])
app.include_router(incident_router, prefix="/api/incidents", tags=["Incidents"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(viewbd_router, prefix="/api/viewbd", tags=["ViewBD"])
app.include_router(prompt_check_router, prefix="/api/prompt-check", tags=["PromptCheck"])

app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/", include_in_schema=False)
def read_index():
    return FileResponse("frontend/index.html")


@app.get("/dashboard", include_in_schema=False)
def read_dashboard():
    return FileResponse("frontend/dashboard.html")


@app.get("/viewbd", include_in_schema=False)
def read_viewbd():
    return FileResponse("frontend/ViewBD.html")


@app.get("/prompt-check", include_in_schema=False)
def read_prompt_check():
    return FileResponse("frontend/PromptCheck.html")

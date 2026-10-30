from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from app.database import init_db
from app.routers import students

STATIC_INDEX_FILE = Path(__file__).parent / "static" / "index.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager that initializes the SQLite database on startup."""
    init_db()
    yield


app = FastAPI(
    title="Students Database CRUD Application",
    description="EWB Internship Project - Students Database CRUD API using Python, FastAPI, and SQLite",
    version="1.0.0",
    lifespan=lifespan,
)

# Include API routers
app.include_router(students.router)


@app.get("/", summary="Root endpoint returning Web Dashboard or API Status")
def read_root(request: Request):
    """Serve the Web Dashboard to browsers, or return JSON status to API clients."""
    accept = request.headers.get("accept", "")
    if accept.startswith("text/html") and STATIC_INDEX_FILE.exists():
        return HTMLResponse(content=STATIC_INDEX_FILE.read_text(encoding="utf-8"))
    return {
        "message": "Welcome to Students Database CRUD Application",
        "status": "running",
    }


@app.get("/dashboard", response_class=HTMLResponse, summary="Interactive Web Dashboard")
def get_dashboard():
    """Direct route for the Interactive Web Dashboard."""
    if STATIC_INDEX_FILE.exists():
        return HTMLResponse(content=STATIC_INDEX_FILE.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Dashboard under maintenance</h1>", status_code=503)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import init_db
from app.routers import students


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


@app.get("/")
def read_root():
    """Root endpoint to verify the API is running."""
    return {
        "message": "Welcome to Students Database CRUD Application",
        "status": "running",
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

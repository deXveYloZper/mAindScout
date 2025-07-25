from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.limiter import limiter
from app.core.database import connect_to_mongo, close_mongo_connection, connect_to_neo4j, close_neo4j_connection
from app.core.ml_models import load_models
from app.api.routers import candidates, jobs, companies, stats, uploads
from app.auth import routes as auth

app = FastAPI(title="mAIndScout API")

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()
    await connect_to_neo4j()
    load_models()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()
    await close_neo4j_connection()

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include all the application routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(uploads.file_upload_router, prefix="/upload", tags=["File Upload"])
app.include_router(candidates.candidate_crud_router, prefix="/candidates", tags=["Candidates"])
app.include_router(jobs.job_crud_router, prefix="/jobs", tags=["Jobs"])
app.include_router(companies.company_crud_router, prefix="/companies", tags=["Companies"])
app.include_router(stats.stats_router, prefix="/stats", tags=["Statistics"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the mAIndScout API"}

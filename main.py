# main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.core.config import Settings
from app.api.endpoints import job_router, candidate_router, file_upload_router
from app.api.endpoints import job_router, candidate_router
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.logging import logger
import logging

logging.basicConfig(filename='my_app.log', level=logging.DEBUG)

# Initialize the rate limiter, which limits the number of requests based on the client's IP address
limiter = Limiter(key_func=get_remote_address)

# Initialize the FastAPI app
app = FastAPI()

# Attach the limiter to the app's state for access throughout the application
app.state.limiter = limiter

# Add an exception handler for when rate limits are exceeded
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware: CORS (Cross-Origin Resource Sharing)
# This middleware allows or restricts resources based on the origin of the request.
# In this case, it allows all origins, but in production, it's recommended to specify the allowed origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1"],  # Consider specifying domains in production for better security
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Middleware: GZip for response compression
# This middleware compresses responses larger than 1000 bytes, which can reduce bandwidth usage and speed up delivery.
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Middleware: Trusted Hosts for additional security
# This middleware only allows requests from specified hosts. It's a security measure to prevent host header attacks.
app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=["example.com", "127.0.0.1", "localhost"]
)

# Include the job router with a prefix, which groups all job-related endpoints under "/job-descriptions"
app.include_router(job_router, prefix="/job-descriptions", tags=["Job Descriptions"])

# Include the candidate router with a prefix, which groups all candidate-related endpoints under "/candidates"
app.include_router(candidate_router, prefix="/candidates", tags=["Candidates"])

#file uploads
app.include_router(file_upload_router, prefix="/upload", tags=["File Uploads"])

# Custom middleware to log requests and responses
# This middleware logs every incoming request's method and URL, and the response's status code.
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Log the request method and URL
    logger.info(f"Request: {request.method} {request.url}")
    
    # Process the request and get the response
    response = await call_next(request)
    
    # Log the response status code
    logger.info(f"Response status: {response.status_code}")
    
    # Return the response to the client
    return response

# Entry point for running the application
if __name__ == "__main__":
    import uvicorn
    # Run the FastAPI app using Uvicorn, a lightning-fast ASGI server
    uvicorn.run(app, host="0.0.0.0", port=8000)

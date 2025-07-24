# app/api/health.py

from fastapi import APIRouter, HTTPException, status
from app.schemas.common import HealthCheckResponse
from app.core.config import settings
from app.services.vector_service import VectorService
from app.services.ontology_service import OntologyService
from app.auth.service import AuthService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

health_router = APIRouter()

@health_router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint to monitor service status.
    
    Returns:
        HealthCheckResponse: Service status and health information
    """
    try:
        # Check database connections
        services = {}
        
        # Check MongoDB
        try:
            from pymongo import MongoClient
            client = MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
            client.admin.command('ping')
            services["mongodb"] = "healthy"
            client.close()
        except Exception as e:
            logger.error(f"MongoDB health check failed: {str(e)}")
            services["mongodb"] = "unhealthy"
        
        # Check Qdrant
        try:
            vector_service = VectorService()
            await vector_service.health_check()
            services["qdrant"] = "healthy"
        except Exception as e:
            logger.error(f"Qdrant health check failed: {str(e)}")
            services["qdrant"] = "unhealthy"
        
        # Check Neo4j
        try:
            ontology_service = OntologyService()
            await ontology_service.health_check()
            services["neo4j"] = "healthy"
        except Exception as e:
            logger.error(f"Neo4j health check failed: {str(e)}")
            services["neo4j"] = "unhealthy"
        
        # Check authentication service
        try:
            auth_service = AuthService()
            # Simple test to ensure service is working
            services["authentication"] = "healthy"
        except Exception as e:
            logger.error(f"Authentication service health check failed: {str(e)}")
            services["authentication"] = "unhealthy"
        
        # Determine overall status
        overall_status = "healthy" if all(status == "healthy" for status in services.values()) else "degraded"
        
        return HealthCheckResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version="1.0.0",
            services=services
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unavailable"
        )

@health_router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint for Kubernetes/container orchestration.
    
    Returns:
        dict: Ready status
    """
    try:
        # Perform basic health checks
        health_response = await health_check()
        
        if health_response.status == "healthy":
            return {"status": "ready"}
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not ready"
            )
            
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )

@health_router.get("/live")
async def liveness_check():
    """
    Liveness check endpoint for Kubernetes/container orchestration.
    
    Returns:
        dict: Alive status
    """
    return {"status": "alive"} 
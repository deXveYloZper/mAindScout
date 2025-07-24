from fastapi import APIRouter, HTTPException, status, Depends, Query, Request
from typing import List, Optional
from app.schemas.job_schema import JobDescription
from app.schemas.common import PaginationParams, PaginatedResponse, SuccessResponse
from app.core.limiter import limiter
from app.api.dependencies import get_job_service
from app.auth.dependencies import get_current_active_user, get_current_recruiter_user
from app.auth.models import User
from app.core.logging import logger
from pydantic import ValidationError
from app.services.enhanced_job_service import EnhancedJobService

job_crud_router = APIRouter()

@job_crud_router.post("/", response_model=JobDescription, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_job(
    request: Request,
    job: JobDescription,
    current_user: User = Depends(get_current_recruiter_user),
    job_service: EnhancedJobService = Depends(get_job_service)
):
    try:
        created_job = await job_service.create_job(job)
        logger.info(f"Job created by {current_user.email}: {created_job.title}")
        return created_job
    except Exception as e:
        logger.error(f"Error creating job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job"
        )

@job_crud_router.get("/", response_model=PaginatedResponse[JobDescription])
@limiter.limit("30/minute")
async def get_jobs(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search query"),
    company: Optional[str] = Query(None, description="Filter by company"),
    location: Optional[str] = Query(None, description="Filter by location"),
    experience_level: Optional[str] = Query(None, description="Filter by experience level"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    sort_by: Optional[str] = Query("created_at", description="Sort field"),
    sort_order: Optional[str] = Query("desc", description="Sort order (asc/desc)"),
    current_user: User = Depends(get_current_active_user),
    job_service: EnhancedJobService = Depends(get_job_service)
):
    try:
        filters = {}
        if company:
            filters["company_name"] = {"$regex": company, "$options": "i"}
        if location:
            filters["location"] = {"$regex": location, "$options": "i"}
        if experience_level:
            filters["experience_level"] = experience_level
        if job_type:
            filters["job_type"] = job_type
        pagination = PaginationParams(page=page, size=size)
        if search:
            result = await job_service.search_jobs(search, pagination, filters)
        else:
            result = await job_service.get_jobs(pagination, filters, sort_by, sort_order)
        return result
    except Exception as e:
        logger.error(f"Error getting jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve jobs"
        )

@job_crud_router.get("/{job_id}", response_model=JobDescription)
@limiter.limit("30/minute")
async def get_job(
    request: Request,
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    job_service: EnhancedJobService = Depends(get_job_service)
):
    try:
        job = await job_service.get_job_by_id(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        return job
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job"
        )

@job_crud_router.put("/{job_id}", response_model=JobDescription)
@limiter.limit("10/minute")
async def update_job(
    request: Request,
    job_id: str,
    job: JobDescription,
    current_user: User = Depends(get_current_recruiter_user),
    job_service: EnhancedJobService = Depends(get_job_service)
):
    try:
        updated_job = await job_service.update_job(job_id, job)
        if not updated_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        logger.info(f"Job updated by {current_user.email}: {job_id}")
        return updated_job
    except Exception as e:
        logger.error(f"Error updating job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update job"
        )

@job_crud_router.delete("/{job_id}", response_model=SuccessResponse)
@limiter.limit("5/minute")
async def delete_job(
    request: Request,
    job_id: str,
    current_user: User = Depends(get_current_recruiter_user),
    job_service: EnhancedJobService = Depends(get_job_service)
):
    try:
        success = await job_service.delete_job(job_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        logger.info(f"Job deleted by {current_user.email}: {job_id}")
        return SuccessResponse(message="Job deleted successfully")
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete job"
        )

@job_crud_router.post("/description", response_model=dict)
@limiter.limit("5/minute")
async def create_job_description(
    request: Request,
    job_description: JobDescription,
    job_service: EnhancedJobService = Depends(get_job_service)
):
    try:
        await job_service.create_job_description(job_description)
        logger.info(f"Job description created: {job_description.title}")
        return {"message": "Job description created successfully"}
    except ValidationError as e:
        logger.error(f"Validation error in create_job_description: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error in create_job_description: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) 
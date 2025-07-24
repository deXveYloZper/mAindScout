from fastapi import APIRouter, HTTPException, status, Depends, Query, Request, BackgroundTasks
from typing import List, Optional
from app.schemas.candidate_schema import CandidateProfile
from app.schemas.common import PaginationParams, PaginatedResponse, SuccessResponse, BulkResponse
from app.schemas.job_schema import JobDescription
from app.schemas.candidate_schema import CandidateMatch
from app.services.candidate_service import CandidateService
from app.auth.dependencies import get_current_active_user, get_current_recruiter_user
from app.auth.models import User
from app.core.logging import logger
from app.core.limiter import limiter
from app.api.dependencies import get_candidate_service, get_job_service
from app.api.dependencies import get_matching_service
from app.services.matching_service import MatchingService

candidate_crud_router = APIRouter()

@candidate_crud_router.post("/", response_model=CandidateProfile, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_candidate(
    request: Request,
    candidate: CandidateProfile,
    current_user: User = Depends(get_current_recruiter_user),
    candidate_service: CandidateService = Depends(get_candidate_service)
):
    try:
        created_candidate = await candidate_service.create_candidate(candidate)
        logger.info(f"Candidate created by {current_user.email}: {created_candidate.name}")
        return created_candidate
    except Exception as e:
        logger.error(f"Error creating candidate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create candidate"
        )

@candidate_crud_router.get("/", response_model=PaginatedResponse[CandidateProfile])
@limiter.limit("30/minute")
async def get_candidates(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search query"),
    skills: Optional[str] = Query(None, description="Filter by skills (comma-separated)"),
    location: Optional[str] = Query(None, description="Filter by location"),
    experience_min: Optional[float] = Query(None, ge=0, description="Minimum experience years"),
    experience_max: Optional[float] = Query(None, ge=0, description="Maximum experience years"),
    sort_by: Optional[str] = Query("created_at", description="Sort field"),
    sort_order: Optional[str] = Query("desc", description="Sort order (asc/desc)"),
    current_user: User = Depends(get_current_active_user),
    candidate_service: CandidateService = Depends(get_candidate_service)
):
    try:
        filters = {}
        if skills:
            skill_list = [s.strip() for s in skills.split(",")]
            filters["skills"] = {"$in": skill_list}
        if location:
            filters["location"] = {"$regex": location, "$options": "i"}
        if experience_min is not None:
            filters["experience_years"] = {"$gte": experience_min}
        if experience_max is not None:
            if "experience_years" in filters:
                filters["experience_years"]["$lte"] = experience_max
            else:
                filters["experience_years"] = {"$lte": experience_max}
        pagination = PaginationParams(page=page, size=size)
        if search:
            result = await candidate_service.search_candidates(search, pagination, filters)
        else:
            result = await candidate_service.get_candidates(pagination, filters, sort_by, sort_order)
        return result
    except Exception as e:
        logger.error(f"Error getting candidates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve candidates"
        )

@candidate_crud_router.get("/{candidate_id}", response_model=CandidateProfile)
@limiter.limit("30/minute")
async def get_candidate(
    request: Request,
    candidate_id: str,
    current_user: User = Depends(get_current_active_user),
    candidate_service: CandidateService = Depends(get_candidate_service)
):
    try:
        candidate = await candidate_service.get_candidate_by_id(candidate_id)
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )
        return candidate
    except Exception as e:
        logger.error(f"Error getting candidate {candidate_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve candidate"
        )

@candidate_crud_router.put("/{candidate_id}", response_model=CandidateProfile)
@limiter.limit("10/minute")
async def update_candidate(
    request: Request,
    candidate_id: str,
    candidate: CandidateProfile,
    current_user: User = Depends(get_current_recruiter_user),
    candidate_service: CandidateService = Depends(get_candidate_service)
):
    try:
        updated_candidate = await candidate_service.update_candidate(candidate_id, candidate)
        if not updated_candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )
        logger.info(f"Candidate updated by {current_user.email}: {candidate_id}")
        return updated_candidate
    except Exception as e:
        logger.error(f"Error updating candidate {candidate_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update candidate"
        )

@candidate_crud_router.delete("/{candidate_id}", response_model=SuccessResponse)
@limiter.limit("5/minute")
async def delete_candidate(
    request: Request,
    candidate_id: str,
    current_user: User = Depends(get_current_recruiter_user),
    candidate_service: CandidateService = Depends(get_candidate_service)
):
    try:
        success = await candidate_service.delete_candidate(candidate_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )
        logger.info(f"Candidate deleted by {current_user.email}: {candidate_id}")
        return SuccessResponse(message="Candidate deleted successfully")
    except Exception as e:
        logger.error(f"Error deleting candidate {candidate_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete candidate"
        )

@candidate_crud_router.post("/bulk", response_model=BulkResponse)
@limiter.limit("5/minute")
async def bulk_create_candidates(
    request: Request,
    candidates: List[CandidateProfile],
    current_user: User = Depends(get_current_recruiter_user),
    candidate_service: CandidateService = Depends(get_candidate_service)
):
    try:
        result = await candidate_service.bulk_create_candidates(candidates)
        logger.info(f"Bulk candidate creation by {current_user.email}: {result['success_count']} created")
        return BulkResponse(**result)
    except Exception as e:
        logger.error(f"Error bulk creating candidates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create candidates"
        )

@candidate_crud_router.post("/match", response_model=dict)
@limiter.limit("2/minute")
async def match_candidates(
    request: Request,
    job_description: JobDescription,
    background_tasks: BackgroundTasks,
    matching_service: MatchingService = Depends(get_matching_service)
):
    try:
        background_tasks.add_task(matching_service.match_candidates, job_description)
        logger.info(f"Started matching candidates for job: {job_description.title}")
        return {"message": "Candidate matching process started"}
    except Exception as e:
        logger.error(f"Error in match_candidates: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@candidate_crud_router.get("/match/{job_id}", response_model=List[CandidateMatch])
@limiter.limit("10/minute")
async def get_matched_candidates(
    request: Request,
    job_id: str,
    matching_service: MatchingService = Depends(get_matching_service)
):
    try:
        matches = await matching_service.get_matched_candidates(job_id)
        if not matches:
            logger.info(f"No matches found for job_id: {job_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No matching candidates found")
        logger.info(f"Retrieved {len(matches)} matches for job_id: {job_id}")
        return matches
    except Exception as e:
        logger.error(f"Error in get_matched_candidates: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) 
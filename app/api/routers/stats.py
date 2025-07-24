from fastapi import APIRouter, HTTPException, status, Depends, Request
from app.schemas.common import StatsResponse
from app.core.limiter import limiter
from app.api.dependencies import get_candidate_service, get_job_service, get_company_service
from app.auth.dependencies import get_current_active_user
from app.core.logging import logger
from datetime import datetime
from app.services.candidate_service import CandidateService
from app.services.enhanced_job_service import EnhancedJobService
from app.services.enhanced_company_service import EnhancedCompanyService

stats_router = APIRouter()

@stats_router.get("/", response_model=StatsResponse)
@limiter.limit("10/minute")
async def get_stats(
    request: Request,
    current_user: str = Depends(get_current_active_user),
    candidate_service: CandidateService = Depends(get_candidate_service),
    job_service: EnhancedJobService = Depends(get_job_service),
    company_service: EnhancedCompanyService = Depends(get_company_service)
):
    try:
        total_candidates = await candidate_service.count_candidates()
        total_jobs = await job_service.count_jobs()
        total_companies = await company_service.count_companies()
        total_matches = 0  # TODO: Implement match counting
        return StatsResponse(
            total_candidates=total_candidates,
            total_jobs=total_jobs,
            total_companies=total_companies,
            total_matches=total_matches,
            last_updated=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        ) 
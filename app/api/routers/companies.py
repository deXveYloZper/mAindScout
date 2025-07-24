from fastapi import APIRouter, HTTPException, status, Depends, Query, Request
from typing import List, Optional
from app.schemas.company_schema import CompanyProfile
from app.schemas.common import PaginationParams, PaginatedResponse, SuccessResponse
from app.core.limiter import limiter
from app.api.dependencies import get_company_service
from app.auth.dependencies import get_current_active_user, get_current_recruiter_user
from app.auth.models import User
from app.core.logging import logger
from app.services.enhanced_company_service import EnhancedCompanyService

company_crud_router = APIRouter()

@company_crud_router.post("/", response_model=CompanyProfile, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_company(
    request: Request,
    company: CompanyProfile,
    current_user: User = Depends(get_current_recruiter_user),
    company_service: EnhancedCompanyService = Depends(get_company_service)
):
    try:
        created_company = await company_service.create_company(company)
        logger.info(f"Company created by {current_user.email}: {created_company.company_name}")
        return created_company
    except Exception as e:
        logger.error(f"Error creating company: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create company"
        )

@company_crud_router.get("/", response_model=PaginatedResponse[CompanyProfile])
@limiter.limit("30/minute")
async def get_companies(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search query"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    location: Optional[str] = Query(None, description="Filter by location"),
    company_size: Optional[str] = Query(None, description="Filter by company size"),
    company_type: Optional[str] = Query(None, description="Filter by company type"),
    sort_by: Optional[str] = Query("created_at", description="Sort field"),
    sort_order: Optional[str] = Query("desc", description="Sort order (asc/desc)"),
    current_user: User = Depends(get_current_active_user),
    company_service: EnhancedCompanyService = Depends(get_company_service)
):
    try:
        filters = {}
        if industry:
            filters["industry"] = {"$regex": industry, "$options": "i"}
        if location:
            filters["location"] = {"$regex": location, "$options": "i"}
        if company_size:
            filters["company_size"] = company_size
        if company_type:
            filters["company_type"] = company_type
        pagination = PaginationParams(page=page, size=size)
        if search:
            result = await company_service.search_companies(search, pagination, filters)
        else:
            result = await company_service.get_companies(pagination, filters, sort_by, sort_order)
        return result
    except Exception as e:
        logger.error(f"Error getting companies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve companies"
        )

@company_crud_router.get("/{company_id}", response_model=CompanyProfile)
@limiter.limit("30/minute")
async def get_company(
    request: Request,
    company_id: str,
    current_user: User = Depends(get_current_active_user),
    company_service: EnhancedCompanyService = Depends(get_company_service)
):
    try:
        company = await company_service.get_company_by_id(company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
        return company
    except Exception as e:
        logger.error(f"Error getting company {company_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve company"
        )

@company_crud_router.put("/{company_id}", response_model=CompanyProfile)
@limiter.limit("10/minute")
async def update_company(
    request: Request,
    company_id: str,
    company: CompanyProfile,
    current_user: User = Depends(get_current_recruiter_user),
    company_service: EnhancedCompanyService = Depends(get_company_service)
):
    try:
        updated_company = await company_service.update_company(company_id, company)
        if not updated_company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
        logger.info(f"Company updated by {current_user.email}: {company_id}")
        return updated_company
    except Exception as e:
        logger.error(f"Error updating company {company_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update company"
        )

@company_crud_router.delete("/{company_id}", response_model=SuccessResponse)
@limiter.limit("5/minute")
async def delete_company(
    request: Request,
    company_id: str,
    current_user: User = Depends(get_current_recruiter_user),
    company_service: EnhancedCompanyService = Depends(get_company_service)
):
    try:
        success = await company_service.delete_company(company_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
        logger.info(f"Company deleted by {current_user.email}: {company_id}")
        return SuccessResponse(message="Company deleted successfully")
    except Exception as e:
        logger.error(f"Error deleting company {company_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete company"
        ) 
# app/services/enhanced_company_service.py

import logging
from typing import List, Optional, Dict, Any
from app.schemas.company_schema import CompanyProfile
from app.schemas.common import PaginationParams, PaginatedResponse
from app.services.base_service import BaseService
from app.services.company_service import CompanyService
from app.core.config import settings

class EnhancedCompanyService(BaseService[CompanyProfile]):
    """
    Enhanced company service that inherits from BaseService for CRUD operations
    while preserving all existing functionality from CompanyService.
    """
    
    def __init__(self):
        """Initialize the enhanced company service."""
        super().__init__("companies")
        self.legacy_service = CompanyService()
        self.logger = logging.getLogger(__name__)

    async def create_company(self, company: CompanyProfile) -> CompanyProfile:
        """Create a new company using the base service."""
        return await self.create(company)

    async def get_company_by_id(self, company_id: str) -> Optional[CompanyProfile]:
        """Get a company by ID using the base service."""
        return await self.get_by_id(company_id)

    async def get_companies(
        self, 
        pagination: PaginationParams = None,
        filters: Dict[str, Any] = None,
        sort_by: str = None,
        sort_order: str = "desc"
    ) -> PaginatedResponse[CompanyProfile]:
        """Get companies with pagination and filtering."""
        return await self.get_all(pagination, filters, sort_by, sort_order)

    async def update_company(self, company_id: str, company: CompanyProfile) -> Optional[CompanyProfile]:
        """Update a company using the base service."""
        return await self.update(company_id, company)

    async def delete_company(self, company_id: str) -> bool:
        """Delete a company using the base service."""
        return await self.delete(company_id)

    async def search_companies(
        self, 
        query: str, 
        pagination: PaginationParams = None,
        filters: Dict[str, Any] = None
    ) -> PaginatedResponse[CompanyProfile]:
        """Search companies by text query."""
        # Combine search query with filters
        search_filters = filters or {}
        search_filters["$text"] = {"$search": query}
        
        return await self.get_all(pagination, search_filters, "score", "desc")

    async def bulk_create_companies(self, companies: List[CompanyProfile]) -> Dict[str, int]:
        """Create multiple companies in bulk."""
        return await self.bulk_create(companies)

    async def count_companies(self, filters: Dict[str, Any] = None) -> int:
        """Count companies with optional filters."""
        return await self.count(filters)

    # Preserve existing functionality from CompanyService
    def import_companies_from_json(self, json_file_path: str) -> Dict[str, int]:
        """Import companies from JSON using legacy service."""
        return self.legacy_service.import_companies_from_json(json_file_path) 
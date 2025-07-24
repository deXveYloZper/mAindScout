# app/services/enhanced_job_service.py

import logging
from typing import List, Optional, Dict, Any
from app.schemas.job_schema import JobDescription
from app.schemas.common import PaginationParams, PaginatedResponse
from app.services.base_service import BaseService
from app.services.job_service import JobService
from app.core.config import settings
from pymongo.database import Database

class EnhancedJobService(BaseService[JobDescription]):
    """
    Enhanced job service that inherits from BaseService for CRUD operations
    while preserving all existing functionality from JobService.
    """
    
    def __init__(self, db: Database):
        """Initialize the enhanced job service."""
        super().__init__("JobDescriptions", db=db)
        self.legacy_service = JobService(db=db)
        self.logger = logging.getLogger(__name__)

    async def create_job(self, job: JobDescription) -> JobDescription:
        """Create a new job using the base service."""
        return await self.create(job)

    async def get_job_by_id(self, job_id: str) -> Optional[JobDescription]:
        """Get a job by ID using the base service."""
        return await self.get_by_id(job_id)

    async def get_jobs(
        self, 
        pagination: PaginationParams = None,
        filters: Dict[str, Any] = None,
        sort_by: str = None,
        sort_order: str = "desc"
    ) -> PaginatedResponse[JobDescription]:
        """Get jobs with pagination and filtering."""
        return await self.get_all(pagination, filters, sort_by, sort_order)

    async def update_job(self, job_id: str, job: JobDescription) -> Optional[JobDescription]:
        """Update a job using the base service."""
        return await self.update(job_id, job)

    async def delete_job(self, job_id: str) -> bool:
        """Delete a job using the base service."""
        return await self.delete(job_id)

    async def search_jobs(
        self, 
        query: str, 
        pagination: PaginationParams = None,
        filters: Dict[str, Any] = None
    ) -> PaginatedResponse[JobDescription]:
        """Search jobs by text query."""
        # Combine search query with filters
        search_filters = filters or {}
        search_filters["$text"] = {"$search": query}
        
        return await self.get_all(pagination, search_filters, "score", "desc")

    async def bulk_create_jobs(self, jobs: List[JobDescription]) -> Dict[str, int]:
        """Create multiple jobs in bulk."""
        return await self.bulk_create(jobs)

    async def count_jobs(self, filters: Dict[str, Any] = None) -> int:
        """Count jobs with optional filters."""
        return await self.count(filters)

    # Preserve existing functionality from JobService
    def create_job_description(self, job_text: str) -> JobDescription:
        """Create job description using legacy service."""
        return self.legacy_service.create_job_description(job_text)

    def get_similar_jobs(self, job_embedding: List[float], limit: int = 10) -> List[Dict]:
        """Get similar jobs using legacy service."""
        return self.legacy_service.get_similar_jobs(job_embedding, limit) 
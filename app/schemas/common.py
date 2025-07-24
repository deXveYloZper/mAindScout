# app/schemas/common.py

from pydantic import BaseModel, Field, GetJsonSchemaHandler, BeforeValidator
from typing import List, Optional, Generic, TypeVar, Any, Annotated
from datetime import datetime
from bson import ObjectId
from pydantic_core import core_schema

T = TypeVar('T')

class PaginationParams(BaseModel):
    """Common pagination parameters for all endpoints."""
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    size: int = Field(default=20, ge=1, le=100, description="Number of items per page")
    skip: Optional[int] = Field(default=None, ge=0, description="Number of items to skip")

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model."""
    items: List[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")

class SearchParams(BaseModel):
    """Common search parameters."""
    query: Optional[str] = Field(default=None, description="Search query")
    filters: Optional[dict] = Field(default_factory=dict, description="Filter criteria")
    sort_by: Optional[str] = Field(default=None, description="Field to sort by")
    sort_order: Optional[str] = Field(default="asc", description="Sort order (asc/desc)")

class BulkResponse(BaseModel):
    """Response model for bulk operations."""
    success_count: int = Field(..., description="Number of successful operations")
    error_count: int = Field(..., description="Number of failed operations")
    errors: List[dict] = Field(default_factory=list, description="List of error details")

class SuccessResponse(BaseModel):
    """Standard success response."""
    message: str = Field(..., description="Success message")
    data: Optional[Any] = Field(default=None, description="Response data")

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Error details")
    code: Optional[str] = Field(default=None, description="Error code")

class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field(..., description="API version")
    services: dict = Field(default_factory=dict, description="Service statuses")

class StatsResponse(BaseModel):
    """Statistics response model."""
    total_candidates: int = Field(..., description="Total number of candidates")
    total_jobs: int = Field(..., description="Total number of jobs")
    total_companies: int = Field(..., description="Total number of companies")
    total_matches: int = Field(..., description="Total number of matches")
    last_updated: datetime = Field(..., description="Last update timestamp")

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: Any
    ) -> core_schema.CoreSchema:
        # This method is called by Pydantic to get a validation schema
        def validate_from_str(value: str) -> ObjectId:
            """Validate a string and convert it to an ObjectId."""
            if ObjectId.is_valid(value):
                return ObjectId(value)
            raise ValueError("Invalid ObjectId")
        # Schema for when the input is already an ObjectId
        from_object_id_schema = core_schema.is_instance_schema(ObjectId)
        # Schema for when the input is a string
        from_str_schema = core_schema.chain_schema([
            core_schema.str_schema(),
            core_schema.no_info_plain_validator_function(validate_from_str),
        ])
        return core_schema.json_or_python_schema(
            json_schema=from_str_schema,
            python_schema=core_schema.union_schema([
                from_object_id_schema,
                from_str_schema,
            ]),
            # This tells Pydantic to serialize ObjectId to a string
            serialization=core_schema.plain_serializer_function_ser_schema(str),
        ) 
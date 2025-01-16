# app/schemas/company_schema.py

from pydantic import BaseModel, Field, HttpUrl, EmailStr
from typing import List, Optional
from datetime import datetime


class TechStackItem(BaseModel):
    technology: str
    type: Optional[str] = None  # e.g., 'frontend', 'backend', 'DevOps'
    level: Optional[str] = None  # e.g., 'primary', 'secondary'


class DomainExpertiseItem(BaseModel):
    domain: str
    confidence_level: Optional[float] = None  # A value between 0 and 1


class GrowthDataPoint(BaseModel):
    date: datetime
    company_size: Optional[str] = None
    funding_total: Optional[float] = None
    tech_stack: List[str] = Field(default_factory=list)
    # Add other relevant fields as needed


class CompanyProfile(BaseModel):
    id: str = Field(..., alias="_id")
    created_at: Optional[datetime] = None
    company_name: str = Field(..., min_length=1, max_length=200, alias='name')
    company_description: Optional[str] = Field(None, alias='short_description')
    industry: List[str] = Field(default_factory=list, alias='categories')
    website: Optional[HttpUrl] = None
    location: List[str] = Field(default_factory=list, alias='locations')
    company_type: Optional[str] = None
    operating_status: Optional[str] = None
    tech_stack: List[TechStackItem] = Field(default_factory=list)
    company_size: Optional[str] = Field(None, alias='num_employees_enum')
    company_culture: List[str] = Field(default_factory=list)
    values: List[str] = Field(default_factory=list)
    domain_expertise: List[DomainExpertiseItem] = Field(default_factory=list)
    founded_on: Optional[datetime] = None
    semrush_global_rank: Optional[float] = None
    semrush_visits_latest_month: Optional[float] = None
    num_investors: Optional[int] = None
    funding_total: Optional[float] = None
    num_exits: Optional[int] = None
    num_funding_rounds: Optional[int] = None
    last_funding_type: Optional[str] = None
    last_funding_at: Optional[datetime] = None
    num_acquisitions: Optional[int] = None
    apptopia_total_apps: Optional[int] = None
    apptopia_total_downloads: Optional[int] = None
    contact_email: Optional[str] = None
    phone_number: Optional[str] = None
    facebook: Optional[HttpUrl] = None
    linkedin: Optional[HttpUrl] = None
    twitter: Optional[HttpUrl] = None
    num_investments: Optional[int] = None
    num_lead_investments: Optional[int] = None
    num_lead_investors: Optional[int] = None
    listed_stock_symbol: Optional[str] = None
    hub_tags: List[str] = Field(default_factory=list)
    ipo_status: Optional[str] = None
    growth_insight_description: Optional[str] = None
    growth_insight_indicator: Optional[str] = None
    growth_insight_direction: Optional[str] = None
    growth_insight_confidence: Optional[str] = None
    investor_insight_description: Optional[str] = None
    permalink: Optional[str] = None
    url: Optional[HttpUrl] = None
    founders: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    partnerships: List[str] = Field(default_factory=list)
    tech_maturity_score: Optional[int] = None
    growth_timeline: List[GrowthDataPoint] = Field(default_factory=list)
    inferred_attributes: List[str] = Field(default_factory=list)
    matching_completeness_score: float = Field(default=0.0)
    general_completeness_score: float = Field(default=0.0)

    class Config:
        populate_by_name = True

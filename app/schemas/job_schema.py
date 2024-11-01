# app/schemas/job_schema.py

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional, Dict
from datetime import datetime, timezone
from bson import ObjectId
from app.schemas.company_schema import CompanyProfile
import re

class JobDescription(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    title: str = Field(..., min_length=5, max_length=100)
    description: str = Field(..., min_length=20, max_length=5000)

    # Skills
    required_skills: List[str] = Field(default_factory=list)
    standardized_skills: List[str] = Field(default_factory=list)
    must_have_skills: List[str] = Field(default_factory=list)  # From version 1
    good_to_have_skills: List[str] = Field(default_factory=list)  # From version 1
    technologies_and_protocols: List[str] = Field(default_factory=list)  # From version 1

    experience_level: Optional[str] = Field(
        None,
        pattern=re.compile(r"^(entry|mid|senior)-level$", re.IGNORECASE)
    )
    experience_years: Optional[str] = None  # From version 1
    responsibilities: List[str] = Field(default_factory=list)
    qualifications: List[str] = Field(default_factory=list)
    
    location: Optional[str] = Field(None, min_length=2, max_length=100)
    company_name: Optional[str] = None
    company_description: Optional[str] = None  # From version 1
    company_industry_focus: List[str] = Field(default_factory=list)  # From version 1
    company_collaborations: List[str] = Field(default_factory=list)  # From version 1
    company_id: Optional[ObjectId] = None
    company_profile: Optional[CompanyProfile] = None

    job_type: Optional[str] = None
    salary_range: Optional[str] = None
    salary_and_benefits: Optional[str] = None  # From version 1
    benefits: List[str] = Field(default_factory=list)
    employment_type: Optional[str] = None
    industry: Optional[str] = None
    education_level: Optional[str] = None
    additional_requirements: Optional[str] = None  # From version 1
    application_instructions: Optional[str] = None  # From version 1
    posting_date: Optional[datetime] = None
    closing_date: Optional[datetime] = None

    # NLP and Classification
    keywords: List[str] = Field(default_factory=list)
    entities: Dict[str, List[str]] = Field(default_factory=dict)
    categories: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(
        populate_by_name=True,
        populate_by_alias=True,  # Ensure this line is included
        from_attributes=True,
        json_encoders={ObjectId: str},
        arbitrary_types_allowed=True
    )

    # Validators...
    @field_validator('title')
    def title_must_be_capitalized(cls, v):
        if not v[0].isupper():
            raise ValueError('Title must start with a capital letter')
        return v

    @field_validator('required_skills')
    def skills_must_be_unique(cls, v):
        if len(v) != len(set(v)):
            raise ValueError('Required skills must be unique')
        return v

    @field_validator('location')
    def location_must_be_valid(cls, v):
        if v and not re.match(r'^[A-Za-z\s,]+$', v):
            raise ValueError('Location must contain only letters, spaces, and commas')
        return v

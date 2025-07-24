# app/schemas/candidate_schema.py

import re
from pydantic import BaseModel, Field, EmailStr, HttpUrl, ConfigDict, field_validator
from typing import List, Optional, Dict
from bson import ObjectId
from datetime import datetime, timezone
from .common import PyObjectId

class EducationItem(BaseModel):
    degree: str
    institution: str
    graduation_year: Optional[int] = None

class Project(BaseModel):
    project_name: str
    description: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    technologies_used: List[str] = Field(default_factory=list)

class WorkExperienceItem(BaseModel):
    company: str
    title: str
    start_date: Optional[str] = None  # 'YYYY-MM-DD' or null
    end_date: Optional[str] = None  # 'YYYY-MM-DD', 'present', or null
    responsibilities: List[str] = Field(default_factory=list)
    company_type: Optional[str] = None  # Added field to store the type of company (e.g., startup, enterprise)
    industry: List[str] = Field(default_factory=list)  # Added field to store industries associated with the company
    tech_stack: List[str] = Field(default_factory=list)  # Added field to store technologies used by the company

class CandidateProfile(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone_number: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    standardized_skills: List[str] = Field(default_factory=list)
    experience_years: Optional[float] = Field(None, ge=0, le=50)
    current_role: Optional[str] = Field(None, min_length=2, max_length=100)
    current_company: Optional[str] = None
    desired_role: Optional[str] = None
    education: List[EducationItem] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    languages: List[Dict[str, str]] = Field(default_factory=list)  # Expecting a list of dictionaries
    # Example of a dictionary format could be {"language": "English", "proficiency": "fluent"}
    summary: Optional[str] = None
    work_experience: List[WorkExperienceItem] = Field(default_factory=list)  # Use updated WorkExperienceItem here
    projects: List[Project] = Field(default_factory=list)
    awards: List[str] = Field(default_factory=list)
    location: Optional[str] = Field(None, min_length=2, max_length=100)
    linkedin_url: Optional[HttpUrl] = None
    github_url: Optional[HttpUrl] = None
    portfolio_url: Optional[HttpUrl] = None
    vector_embedding: Optional[List[float]] = Field(None, description="Compressed embedding vector")
    keywords: List[str] = Field(default_factory=list)
    entities: Dict[str, List[str]] = Field(default_factory=dict)
    categories: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )

    # Validator for the 'name' field to ensure it only contains letters, spaces, hyphens, and apostrophes
    @field_validator('name')
    def name_must_be_valid(cls, v):
        if not re.match(r'^[A-Za-z\s\'-]+$', v):
            raise ValueError('Name must contain only letters, spaces, hyphens, and apostrophes')
        return v

    # Validator for the 'skills' field to ensure that each skill in the list is unique
    @field_validator('skills')
    def skills_must_be_unique(cls, v):
        if len(v) != len(set(v)):
            raise ValueError('Skills must be unique')
        return v

class CandidateMatch(BaseModel):
    candidate: CandidateProfile
    score: float = Field(..., ge=0, le=1)

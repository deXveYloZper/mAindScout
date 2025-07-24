# app/core/models.py
from pydantic import BaseModel, HttpUrl, Field, EmailStr
from typing import List, Optional
from datetime import datetime
from beanie import Document, Indexed
from pymongo import IndexModel, ASCENDING, TEXT


class JobDescription(BaseModel):
    title: str = Field(..., description="The title of the job position", min_length=1, strip_whitespace=True)
    description: str = Field(..., description="A detailed description of the job responsibilities and requirements", min_length=1, strip_whitespace=True)
    required_skills: List[str] = Field(default_factory=list, description="A list of required skills for the job")
    experience_level: Optional[str] = Field(None, description="The experience level required for the job", min_length=1, strip_whitespace=True)
    location: Optional[str] = Field(None, description="The location of the job", min_length=1, strip_whitespace=True)
    company_name: Optional[str] = Field(None, description="The name of the hiring company", min_length=1, strip_whitespace=True)
    job_type: Optional[str] = Field(None, description="The type of job (e.g., full-time, part-time, contract)", min_length=1, strip_whitespace=True)
    salary_range: Optional[str] = Field(None, description="The salary range for the job", min_length=1, strip_whitespace=True)
    benefits: Optional[List[str]] = Field(default_factory=list, description="List of benefits offered by the job")
    qualifications: Optional[List[str]] = Field(default_factory=list, description="List of qualifications required for the job")
    responsibilities: Optional[List[str]] = Field(default_factory=list, description="Key responsibilities of the job")
    employment_type: Optional[str] = Field(None, description="Employment type (e.g., Permanent, Contract)")
    industry: Optional[str] = Field(None, description="Industry related to the job")
    education_level: Optional[str] = Field(None, description="Required education level for the job")
    posting_date: Optional[str] = Field(None, description="The date when the job was posted")
    closing_date: Optional[str] = Field(None, description="The application deadline for the job")

# Define a Pydantic model for a Candidate Profile
class CandidateProfile(BaseModel):
    name: str = Field(..., description="The candidate's full name", min_length=1, strip_whitespace=True)
    email: str = Field(..., description="The candidate's email address", pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$", min_length=1, strip_whitespace=True)

    # Core Skills & Experience
    skills: List[str] = Field(default_factory=list, description="A list of skills that the candidate possesses")
    experience_years: int = Field(default=0, description="The number of years of experience the candidate has in their field", ge=0)
    current_role: Optional[str] = Field(None, description="The candidate's current job role", min_length=1, strip_whitespace=True)
    current_company: Optional[str] = Field(None, description="The candidate's current company", min_length=1, strip_whitespace=True) 
    desired_role: Optional[str] = Field(None, description="The candidate's desired or target job role", min_length=1, strip_whitespace=True)  
    industry_experience: List[str] = Field(default_factory=list, description="Industries the candidate has worked in") 

    # Location & Mobility
    location: Optional[str] = Field(None, description="The candidate's current location", min_length=1, strip_whitespace=True)
    relocation_willingness: Optional[bool] = Field(None, description="Indicates if the candidate is willing to relocate for a job")
    work_authorization: Optional[str] = Field(None, description="Candidate's work authorization status (e.g., 'US Citizen', 'H1B Visa')") 

    #  Vector Embedding for Similarity Matching (Keep as is)
    vector_embedding: Optional[List[float]] = Field(default_factory=lambda: [0.0]*128, description="Vector embedding for similarity matching", min_items=128, max_items=128)

    # Richer Textual Information
    professional_summary: Optional[str] = Field(None, description="A brief summary of the candidate's professional experience", min_length=1, strip_whitespace=True)
    cover_letter: Optional[str] = Field(None, description="Candidate's cover letter, if available")  

    # Structured Work & Education History 
    work_experience: Optional[List[dict]] = Field(default_factory=list, description="A list of work experiences with details")
    """
    Example work_experience item:
    {
        "company": "Acme Corp",
        "title": "Software Engineer",
        "start_date": "2020-01-01",
        "end_date": "2023-06-30", 
        "description": "Developed and maintained key features of the company's flagship product...", 
        "achievements": ["Led a team of 5 engineers...", "Increased product performance by 20%..."] 
    }
    """
    education: Optional[List[dict]] = Field(default_factory=list, description="A list of educational qualifications") 
    """
    Example education item:
    {
        "degree": "Bachelor of Science in Computer Science",
        "institution": "Stanford University",
        "graduation_year": 2019 
    }
    """

    # Additional Details
    certifications: Optional[List[str]] = Field(default_factory=list, description="A list of certifications")
    languages: Optional[List[dict]] = Field(default_factory=list, description="A list of languages") 
    """
    Example languages item:
    {
        "language": "Spanish",
        "proficiency": "Fluent" 
    }
    """
    interests: Optional[List[str]] = Field(default_factory=list, description="Candidate's professional interests or areas of focus")
    projects: Optional[List[dict]] = Field(default_factory=list, description="Personal or professional projects the candidate has worked on")
    """
    Example projects item:
    {
        "name": "Open-Source Contribution to XYZ Library",
        "description": "Contributed new features and bug fixes...",
        "url": "https://github.com/..." 
    }
    """
    publications: Optional[List[dict]] = Field(default_factory=list, description="Any publications or research papers the candidate has authored")
    """
    Example publications item:
    {
        "title": "Machine Learning for Predictive Analytics",
        "journal": "Journal of Data Science",
        "year": 2022
    }
    """
    awards: Optional[List[str]] = Field(default_factory=list, description="Awards or recognitions the candidate has received")
    volunteer_experience: Optional[List[dict]] = Field(default_factory=list, description="Volunteer work the candidate has done")
    references: Optional[List[dict]] = Field(default_factory=list, description="Professional references, if provided")
    """
    Example references item:
    {
        "name": "John Doe",
        "company": "ABC Company",
        "title": "Senior Manager",
        "email": "john.doe@abccompany.com"
    }
    """
    
    # Additional Notes/Flags
    #last_updated: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the last profile update")
    is_active: bool = Field(default=True, description="Indicates if the candidate is actively seeking opportunities") 

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


class CompanyProfile(Document):
    id: str = Field(..., alias='id')
    created_at: Optional[datetime] = None
    company_name: str = Field(..., min_length=1, max_length=200)
    company_description: Optional[str] = None
    industry: List[str] = Field(default_factory=list)
    website: Optional[HttpUrl] = None
    location: List[str] = Field(default_factory=list)
    company_type: Optional[str] = None
    operating_status: Optional[str] = None
    tech_stack: List[TechStackItem] = Field(default_factory=list)
    company_size: Optional[str] = None
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

    class Settings:
        name = "companies"
        indexes = [
            # Single-field indexes on array fields
            IndexModel([("industry", ASCENDING)], name="industry_index"),
            IndexModel([("location", ASCENDING)], name="location_index"),
            IndexModel([("tech_stack.technology", ASCENDING)], name="tech_stack_technology_index"),
            # Single-field indexes on scalar fields
            IndexModel([("company_size", ASCENDING)], name="company_size_index"),
            IndexModel([("operating_status", ASCENDING)], name="operating_status_index"),
            IndexModel([("company_type", ASCENDING)], name="company_type_index"),
            IndexModel([("tech_maturity_score", ASCENDING)], name="tech_maturity_score_index"),
            # Expanded text index for search and matching
            IndexModel(
                [
                    ("company_name", TEXT),
                    ("company_description", TEXT),
                    ("industry", TEXT),
                    ("tags", TEXT),
                    ("tech_stack.technology", TEXT),
                    ("location", TEXT),
                ],
                name="text_search_index",
                default_language="english"
            ),
        ]

    class Config:
        populate_by_name = True
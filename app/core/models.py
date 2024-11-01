# app/core/models.py
from pydantic import BaseModel, Field
from typing import List, Optional

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


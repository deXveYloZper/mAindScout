# app/services/matching_service.py

from app.schemas.candidate_schema import CandidateProfile
from app.schemas.job_schema import JobDescription

class MatchingService:
    def __init__(self):
        pass

    def match_candidate_to_job(self, candidate_profile: CandidateProfile, job_description: JobDescription) -> float:
        """
        Compute a match score between a candidate and a job description.

        Args:
        - candidate_profile: CandidateProfile object.
        - job_description: JobDescription object.

        Returns:
        - match_score: float between 0 and 1.
        """
        # Convert standardized skills to sets
        candidate_skills = set(candidate_profile.standardized_skills or [])
        job_skills = set(job_description.standardized_skills or [])

        if not job_skills:
            return 0.0

        # Calculate skill match score
        skill_match_count = len(candidate_skills & job_skills)
        total_job_skills = len(job_skills)
        skill_match_score = skill_match_count / total_job_skills

        # Optionally, incorporate other factors
        # For example, experience level, location, keywords, etc.

        # For now, we'll return the skill match score
        return skill_match_score

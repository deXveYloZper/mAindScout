# app/services/candidate_evaluation_service.py

import logging
from app.core.models import CandidateProfile
from datetime import datetime
from typing import Optional, List

class CandidateEvaluationService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def evaluate_candidate(self, candidate_profile: CandidateProfile, target_role: Optional[str] = None) -> float:
        """
        Evaluate a candidate's profile and return a final score based on different criteria.
        The score will be normalized to a scale of 1-10.
        """
        total_score = 0
        total_weight = 0

        # Step 1: Determine Experience Level
        experience_years = candidate_profile.experience_years or 0
        experience_level = self.get_experience_level(experience_years)

        # Step 2: Seniority Evaluation
        seniority_score, seniority_weight = self.evaluate_seniority(experience_years, experience_level)
        total_score += seniority_score * seniority_weight
        total_weight += seniority_weight

        # Step 3: Job Stability vs. Hopping
        job_stability_score, job_stability_weight = self.evaluate_job_stability(candidate_profile.work_experience, experience_level)
        total_score += job_stability_score * job_stability_weight
        total_weight += job_stability_weight

        # Step 4: Industry Experience
        industry_score, industry_weight = self.evaluate_industry_experience(candidate_profile.industry_experience)
        total_score += industry_score * industry_weight
        total_weight += industry_weight

        # Step 5: Technology Relevance Evaluation
        tech_score, tech_weight = self.evaluate_technology_experience(candidate_profile.skills, candidate_profile.work_experience, target_role)
        total_score += tech_score * tech_weight
        total_weight += tech_weight

        # Step 6: Role Relevance Evaluation
        role_relevance_score, role_relevance_weight = self.evaluate_role_relevance(candidate_profile.work_experience, target_role)
        total_score += role_relevance_score * role_relevance_weight
        total_weight += role_relevance_weight

        # Normalize the score to a scale of 1-10
        if total_weight == 0:
            return 1.0  # Minimum score if no information is available
        final_score = (total_score / total_weight) * 10
        return round(final_score, 2)

    def get_experience_level(self, experience_years: int) -> str:
        """
        Determine the experience level based on years of experience.
        """
        if experience_years <= 3:
            return "junior"
        elif 4 <= experience_years <= 8:
            return "mid"
        else:
            return "senior"

    def evaluate_seniority(self, experience_years: int, experience_level: str) -> tuple:
        """
        Score candidates based on their total years of experience and experience level.
        """
        if experience_level == "junior":
            if experience_years <= 1:
                return 4, 1  # Early-stage junior
            elif 1 < experience_years <= 3:
                return 6, 1  # Late-stage junior
        elif experience_level == "mid":
            if 4 <= experience_years <= 6:
                return 7, 1  # Early-stage mid-level
            else:
                return 8, 1  # Late-stage mid-level
        else:  # Senior
            if experience_years <= 10:
                return 8, 1  # Early-stage senior
            else:
                return 10, 1  # Highly experienced senior

        return 1, 1  # Default score if experience years are unclear

    def evaluate_job_stability(self, work_experience: List[dict], experience_level: str) -> tuple:
        """
        Evaluate job stability based on average tenure in each role.
        """
        if not work_experience:
            return 3, 1  # No work experience, default weight for juniors

        total_tenure = 0
        total_roles = len(work_experience)

        for role in work_experience:
            start_date = self.parse_date(role['start_date'])
            end_date = self.parse_date(role['end_date']) if role['end_date'].lower() != "present" else datetime.now()

            if start_date and end_date:
                tenure_years = (end_date - start_date).days / 365.25
                total_tenure += tenure_years

        if total_roles == 0:
            return 3, 1  # Default score for missing data

        average_tenure = total_tenure / total_roles

        # Scoring based on average tenure
        if experience_level == "junior":
            if average_tenure >= 1.5:
                return 8, 1  # Good stability for junior
            elif 1.0 <= average_tenure < 1.5:
                return 6, 1  # Moderate stability for junior
            else:
                return 4, 1  # Poor stability for junior
        else:
            if average_tenure >= 2.5:
                return 10, 1  # Good stability for mid/senior
            elif 1.5 <= average_tenure < 2.5:
                return 7, 1  # Moderate stability for mid/senior
            else:
                return 5, 1  # Poor stability for mid/senior

    def evaluate_industry_experience(self, industry_experience: List[str]) -> tuple:
        """
        Evaluate candidates based on their experience in different industries and continuity in a particular domain.
        """
        if not industry_experience:
            return 3, 1  # No industry experience, default weight

        unique_industries = set(industry_experience)
        industry_count = len(unique_industries)

        # Scoring based on the number of industries and consistency
        if industry_count == 1:
            return 10, 1  # High consistency in a particular domain
        elif 2 <= industry_count <= 3:
            return 7, 1  # Moderate variety
        else:
            return 5, 1  # High variety, less specialization

    def evaluate_technology_experience(self, skills: List[str], work_experience: List[dict], target_role: Optional[str]) -> tuple:
        """
        Evaluate candidates based on the relevance and depth of their technology experience.
        """
        if not skills:
            return 3, 1  # Default score if no skills are provided

        tech_weight = 1.0
        role_relevance = 0
        for skill in skills:
            # Check if the skill matches the target role requirements
            if target_role and skill.lower() in target_role.lower():
                role_relevance += 1

        # Weight technology depth based on consistency in work experience
        tech_depth_score = min(len(skills), 10)  # Limit max score to 10
        return tech_depth_score, tech_weight

    def evaluate_role_relevance(self, work_experience: List[dict], target_role: Optional[str]) -> tuple:
        """
        Evaluate role relevance based on how closely the candidate's work experience aligns with the target role.
        """
        if not target_role or not work_experience:
            return 5, 1  # Default score if no target role is provided

        relevance_score = 0
        weight = 1.5  # Higher weight for role relevance

        for role in work_experience:
            if target_role.lower() in role['title'].lower():
                relevance_score += 2  # Increase score for matching title
            elif any(word in target_role.lower() for word in role['title'].lower().split()):
                relevance_score += 1  # Partial match

        # Normalize relevance score to 10
        relevance_score = min(relevance_score, 10)
        return relevance_score, weight

    def parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Helper function to parse date strings in YYYY-MM-DD format.
        """
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return None

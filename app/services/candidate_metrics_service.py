# app/services/candidate_metrics_service.py

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from app.services.entity_normalization_service import EntityNormalizationService
from app.services.ontology_service import OntologyService
import re

logger = logging.getLogger(__name__)


class CandidateMetricsService:
    """
    Service for calculating derived metrics for candidate profiles.
    Builds upon existing evaluation logic to provide comprehensive candidate scoring.
    """
    
    def __init__(self, entity_normalization: EntityNormalizationService, ontology_service: OntologyService):
        """Initialize the entity normalization and ontology services for metrics calculation."""
        self.entity_normalization = entity_normalization
        self.ontology_service = ontology_service
        self.logger = logging.getLogger(__name__)
        
        # Domain keyword sets for relevant experience calculation
        self.domain_keywords = {
            "software_development": {
                "developer", "engineer", "sde", "programmer", "coder", "software",
                "full stack", "frontend", "backend", "fullstack", "web developer",
                "application developer", "systems developer"
            },
            "data_science": {
                "data scientist", "data analyst", "ml engineer", "machine learning",
                "ai engineer", "statistician", "quantitative analyst", "bi analyst",
                "data engineer", "analytics engineer"
            },
            "devops": {
                "devops", "site reliability engineer", "sre", "platform engineer",
                "infrastructure engineer", "cloud engineer", "systems engineer",
                "release engineer", "build engineer"
            },
            "product_management": {
                "product manager", "product owner", "technical product manager",
                "program manager", "project manager", "product lead", "pm"
            },
            "design": {
                "ui designer", "ux designer", "product designer", "interaction designer",
                "visual designer", "designer", "creative director"
            },
            "qa_testing": {
                "qa engineer", "test engineer", "quality assurance", "software tester",
                "test automation engineer", "sdet", "quality engineer"
            }
        }
    
    def calculate_candidate_metrics(self, candidate_profile: Dict) -> Dict:
        """
        Calculate comprehensive metrics for a candidate profile.
        
        Args:
            candidate_profile: The candidate profile dictionary
            
        Returns:
            Dict: Calculated metrics including experience, tenure, and scores
        """
        try:
            metrics = {}
            
            # Calculate experience metrics
            experience_metrics = self._calculate_experience_metrics(candidate_profile)
            metrics.update(experience_metrics)
            
            # Calculate tenure metrics
            tenure_metrics = self._calculate_tenure_metrics(candidate_profile)
            metrics.update(tenure_metrics)
            
            # Calculate universal profile score
            universal_score = self._calculate_universal_profile_score(
                candidate_profile, experience_metrics, tenure_metrics
            )
            metrics["universal_profile_score"] = universal_score
            
            # Calculate seniority level
            seniority_level = self._determine_seniority_level(
                experience_metrics["total_experience_years"]
            )
            metrics["seniority_level"] = seniority_level
            
            # Calculate career progression score
            progression_score = self._calculate_career_progression_score(candidate_profile)
            metrics["career_progression_score"] = progression_score
            
            # Calculate company prestige score
            prestige_score = self._calculate_company_prestige_score(candidate_profile)
            metrics["company_prestige_score"] = prestige_score
            
            # Calculate skill depth score
            skill_depth_score = self._calculate_skill_depth_score(candidate_profile)
            metrics["skill_depth_score"] = skill_depth_score
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating candidate metrics: {str(e)}")
            return self._get_default_metrics()
    
    def _calculate_experience_metrics(self, candidate_profile: Dict) -> Dict:
        """
        Calculate experience-related metrics.
        
        Args:
            candidate_profile: The candidate profile
            
        Returns:
            Dict: Experience metrics
        """
        work_experience = candidate_profile.get("work_experience", [])
        
        # Calculate total experience years
        total_experience_years = self._calculate_total_experience_years(work_experience)
        
        # Calculate relevant experience years for different domains
        relevant_experience = {}
        for domain, keywords in self.domain_keywords.items():
            relevant_years = self._calculate_relevant_experience_years(work_experience, keywords)
            relevant_experience[domain] = relevant_years
        
        # Calculate overall relevant experience (max across domains)
        overall_relevant_years = max(relevant_experience.values()) if relevant_experience else 0.0
        
        return {
            "total_experience_years": total_experience_years,
            "relevant_experience_years": overall_relevant_years,
            "domain_relevant_experience": relevant_experience
        }
    
    def _calculate_total_experience_years(self, work_experience: List[Dict]) -> float:
        """
        Calculate total years of work experience.
        
        Args:
            work_experience: List of work experience entries
            
        Returns:
            float: Total experience years
        """
        total_years = 0.0
        
        for exp in work_experience:
            start_date = self._parse_date(exp.get("start_date"))
            end_date = self._parse_date(exp.get("end_date"))
            
            if start_date and end_date:
                duration = end_date - start_date
                total_years += duration.days / 365.25
            elif start_date:
                # If no end date, assume current date
                duration = datetime.now() - start_date
                total_years += duration.days / 365.25
        
        return round(total_years, 2)
    
    def _calculate_relevant_experience_years(self, work_experience: List[Dict], domain_keywords: set) -> float:
        """
        Calculate relevant experience years for a specific domain.
        
        Args:
            work_experience: List of work experience entries
            domain_keywords: Set of keywords for the domain
            
        Returns:
            float: Relevant experience years
        """
        relevant_years = 0.0
        
        for exp in work_experience:
            job_title = exp.get("title", "").lower()
            responsibilities = " ".join(exp.get("responsibilities", [])).lower()
            
            # Check if job title or responsibilities contain domain keywords
            is_relevant = any(keyword in job_title for keyword in domain_keywords) or \
                         any(keyword in responsibilities for keyword in domain_keywords)
            
            if is_relevant:
                start_date = self._parse_date(exp.get("start_date"))
                end_date = self._parse_date(exp.get("end_date"))
                
                if start_date and end_date:
                    duration = end_date - start_date
                    relevant_years += duration.days / 365.25
                elif start_date:
                    duration = datetime.now() - start_date
                    relevant_years += duration.days / 365.25
        
        return round(relevant_years, 2)
    
    def _calculate_tenure_metrics(self, candidate_profile: Dict) -> Dict:
        """
        Calculate tenure-related metrics.
        
        Args:
            candidate_profile: The candidate profile
            
        Returns:
            Dict: Tenure metrics
        """
        work_experience = candidate_profile.get("work_experience", [])
        
        if not work_experience:
            return {
                "average_tenure_months": 0.0,
                "longest_tenure_months": 0.0,
                "job_stability_score": 0.0,
                "tenure_distribution": []
            }
        
        tenures = []
        for exp in work_experience:
            start_date = self._parse_date(exp.get("start_date"))
            end_date = self._parse_date(exp.get("end_date"))
            
            if start_date and end_date:
                duration = end_date - start_date
                tenure_months = duration.days / 30.44  # Average days per month
                tenures.append(tenure_months)
            elif start_date:
                duration = datetime.now() - start_date
                tenure_months = duration.days / 30.44
                tenures.append(tenure_months)
        
        if not tenures:
            return {
                "average_tenure_months": 0.0,
                "longest_tenure_months": 0.0,
                "job_stability_score": 0.0,
                "tenure_distribution": []
            }
        
        average_tenure = sum(tenures) / len(tenures)
        longest_tenure = max(tenures)
        
        # Calculate job stability score (0-10)
        # Higher score for longer average tenure and fewer job changes
        stability_score = min(10.0, (average_tenure / 12.0) * 5.0 + (len(work_experience) / 10.0) * 5.0)
        
        return {
            "average_tenure_months": round(average_tenure, 2),
            "longest_tenure_months": round(longest_tenure, 2),
            "job_stability_score": round(stability_score, 2),
            "tenure_distribution": [round(t, 2) for t in tenures]
        }
    
    def _calculate_universal_profile_score(self, candidate_profile: Dict, experience_metrics: Dict, tenure_metrics: Dict) -> float:
        """
        Calculate the universal profile score based on multiple factors.
        
        Args:
            candidate_profile: The candidate profile
            experience_metrics: Calculated experience metrics
            tenure_metrics: Calculated tenure metrics
            
        Returns:
            float: Universal profile score (0-10)
        """
        # Get seniority level for weight adjustment
        seniority_level = self._determine_seniority_level(experience_metrics["total_experience_years"])
        
        # Define weights based on seniority level
        weights = self._get_seniority_weights(seniority_level)
        
        # Calculate sub-scores
        experience_score = self._calculate_experience_score(experience_metrics)
        stability_score = self._calculate_stability_score(tenure_metrics)
        progression_score = self._calculate_career_progression_score(candidate_profile)
        prestige_score = self._calculate_company_prestige_score(candidate_profile)
        skill_score = self._calculate_skill_depth_score(candidate_profile)
        
        # Calculate weighted score
        total_score = (
            weights["experience"] * experience_score +
            weights["stability"] * stability_score +
            weights["progression"] * progression_score +
            weights["prestige"] * prestige_score +
            weights["skills"] * skill_score
        )
        
        return round(total_score, 2)
    
    def _determine_seniority_level(self, total_experience_years: float) -> str:
        """
        Determine seniority level based on experience years.
        
        Args:
            total_experience_years: Total years of experience
            
        Returns:
            str: Seniority level (Junior, Mid, Senior)
        """
        if total_experience_years <= 3:
            return "Junior"
        elif total_experience_years <= 8:
            return "Mid"
        else:
            return "Senior"
    
    def _get_seniority_weights(self, seniority_level: str) -> Dict[str, float]:
        """
        Get scoring weights based on seniority level.
        
        Args:
            seniority_level: The seniority level
            
        Returns:
            Dict[str, float]: Weights for different factors
        """
        if seniority_level == "Junior":
            return {
                "experience": 0.3,
                "stability": 0.2,
                "progression": 0.2,
                "prestige": 0.1,
                "skills": 0.2
            }
        elif seniority_level == "Mid":
            return {
                "experience": 0.25,
                "stability": 0.25,
                "progression": 0.25,
                "prestige": 0.15,
                "skills": 0.1
            }
        else:  # Senior
            return {
                "experience": 0.2,
                "stability": 0.2,
                "progression": 0.3,
                "prestige": 0.2,
                "skills": 0.1
            }
    
    def _calculate_experience_score(self, experience_metrics: Dict) -> float:
        """
        Calculate experience sub-score (0-10).
        
        Args:
            experience_metrics: Experience metrics
            
        Returns:
            float: Experience score
        """
        total_years = experience_metrics["total_experience_years"]
        relevant_years = experience_metrics["relevant_experience_years"]
        
        # Base score on total experience
        base_score = min(10.0, total_years / 2.0)
        
        # Bonus for relevant experience
        relevance_bonus = min(2.0, relevant_years / total_years * 2.0) if total_years > 0 else 0.0
        
        return min(10.0, base_score + relevance_bonus)
    
    def _calculate_stability_score(self, tenure_metrics: Dict) -> float:
        """
        Calculate stability sub-score (0-10).
        
        Args:
            tenure_metrics: Tenure metrics
            
        Returns:
            float: Stability score
        """
        return tenure_metrics.get("job_stability_score", 0.0)
    
    def _calculate_career_progression_score(self, candidate_profile: Dict) -> float:
        """
        Calculate career progression score (0-10).
        
        Args:
            candidate_profile: The candidate profile
            
        Returns:
            float: Progression score
        """
        work_experience = candidate_profile.get("work_experience", [])
        
        if len(work_experience) < 2:
            return 5.0  # Neutral score for single job
        
        # Sort by start date
        sorted_experience = sorted(work_experience, key=lambda x: self._parse_date(x.get("start_date")) or datetime.min)
        
        # Analyze progression through job titles
        progression_score = 0.0
        for i in range(1, len(sorted_experience)):
            prev_title = sorted_experience[i-1].get("title", "").lower()
            curr_title = sorted_experience[i].get("title", "").lower()
            
            # Check for progression indicators
            if any(word in curr_title for word in ["senior", "lead", "principal", "manager", "director"]):
                if not any(word in prev_title for word in ["senior", "lead", "principal", "manager", "director"]):
                    progression_score += 2.0  # Clear progression
                else:
                    progression_score += 1.0  # Lateral move at senior level
            elif "junior" in prev_title and "junior" not in curr_title:
                progression_score += 1.5  # Junior to regular
        
        # Normalize to 0-10 scale
        max_possible_progression = (len(sorted_experience) - 1) * 2.0
        if max_possible_progression > 0:
            progression_score = (progression_score / max_possible_progression) * 10.0
        
        return min(10.0, progression_score)
    
    def _calculate_company_prestige_score(self, candidate_profile: Dict) -> float:
        """
        Calculate company prestige score (0-10).
        
        Args:
            candidate_profile: The candidate profile
            
        Returns:
            float: Prestige score
        """
        work_experience = candidate_profile.get("work_experience", [])
        
        if not work_experience:
            return 5.0  # Neutral score
        
        # Define company tiers (simplified)
        tier_1_companies = {"google", "microsoft", "apple", "amazon", "meta", "facebook", "netflix", "tesla"}
        tier_2_companies = {"uber", "airbnb", "stripe", "square", "slack", "zoom", "salesforce", "oracle"}
        
        prestige_scores = []
        for exp in work_experience:
            company_name = exp.get("company", "").lower()
            
            if any(tier1 in company_name for tier1 in tier_1_companies):
                prestige_scores.append(10.0)
            elif any(tier2 in company_name for tier2 in tier_2_companies):
                prestige_scores.append(8.0)
            else:
                # Check company size and other factors
                company_type = exp.get("company_type", "")
                if company_type in ["startup", "scaleup"]:
                    prestige_scores.append(6.0)
                elif company_type in ["enterprise", "fortune500"]:
                    prestige_scores.append(7.0)
                else:
                    prestige_scores.append(5.0)
        
        return sum(prestige_scores) / len(prestige_scores) if prestige_scores else 5.0
    
    def _calculate_skill_depth_score(self, candidate_profile: Dict) -> float:
        """
        Calculate skill depth score (0-10).
        
        Args:
            candidate_profile: The candidate profile
            
        Returns:
            float: Skill depth score
        """
        skills = candidate_profile.get("skills", [])
        standardized_skills = candidate_profile.get("standardized_skills", [])
        
        # Count unique skills
        unique_skills = len(set(skills + standardized_skills))
        
        # Score based on skill breadth and depth
        if unique_skills >= 15:
            return 10.0
        elif unique_skills >= 10:
            return 8.0
        elif unique_skills >= 5:
            return 6.0
        elif unique_skills >= 2:
            return 4.0
        else:
            return 2.0
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse date string to datetime object.
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            Optional[datetime]: Parsed datetime or None
        """
        if not date_str or date_str.lower() == "present":
            return None
        
        # Try common date formats
        date_formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%Y-%m",
            "%m/%Y",
            "%Y"
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def _get_default_metrics(self) -> Dict:
        """
        Get default metrics when calculation fails.
        
        Returns:
            Dict: Default metrics
        """
        return {
            "total_experience_years": 0.0,
            "relevant_experience_years": 0.0,
            "domain_relevant_experience": {},
            "average_tenure_months": 0.0,
            "longest_tenure_months": 0.0,
            "job_stability_score": 0.0,
            "tenure_distribution": [],
            "universal_profile_score": 0.0,
            "seniority_level": "Junior",
            "career_progression_score": 0.0,
            "company_prestige_score": 0.0,
            "skill_depth_score": 0.0
        }
    
    def health_check(self) -> bool:
        """
        Perform a health check on the metrics service.
        
        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            return self.entity_normalization.health_check()
        except Exception as e:
            self.logger.error(f"Candidate metrics health check failed: {str(e)}")
            return False
    
    def close(self):
        """Close the entity normalization service connection."""
        self.entity_normalization.close() 
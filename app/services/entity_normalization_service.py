# app/services/entity_normalization_service.py

import logging
from typing import List, Dict, Optional, Tuple
from app.services.ontology_service import OntologyService
from rapidfuzz import fuzz, process
import re

logger = logging.getLogger(__name__)


class EntityNormalizationService:
    """
    Service for normalizing extracted entities to canonical forms using the ontology.
    Provides fuzzy matching and entity resolution capabilities.
    """
    
    def __init__(self, ontology_service):
        """Initialize the ontology service for entity normalization."""
        self.ontology_service = ontology_service
        self.logger = logging.getLogger(__name__)
    
    async def normalize_skills(self, skills: List[str], fuzzy_threshold: float = 80.0) -> List[Dict[str, str]]:
        """
        Normalize a list of skills to their canonical forms.
        
        Args:
            skills: List of skill names to normalize
            fuzzy_threshold: Minimum similarity score for fuzzy matching
            
        Returns:
            List[Dict[str, str]]: List of normalized skills with original and canonical forms
        """
        normalized_skills = []
        
        for skill in skills:
            if not skill or not skill.strip():
                continue
                
            # Clean the skill name
            cleaned_skill = self._clean_entity_name(skill)
            
            # Try exact normalization first
            canonical_skill = await self.ontology_service.normalize_skill(cleaned_skill)
            
            if canonical_skill:
                normalized_skills.append({
                    "original": skill,
                    "canonical": canonical_skill,
                    "confidence": 1.0,
                    "match_type": "exact"
                })
            else:
                # Try fuzzy matching
                fuzzy_match = self._fuzzy_match_skill(cleaned_skill, fuzzy_threshold)
                if fuzzy_match:
                    normalized_skills.append({
                        "original": skill,
                        "canonical": fuzzy_match["canonical"],
                        "confidence": fuzzy_match["confidence"],
                        "match_type": "fuzzy"
                    })
                else:
                    # Keep original if no match found
                    normalized_skills.append({
                        "original": skill,
                        "canonical": skill,
                        "confidence": 0.0,
                        "match_type": "none"
                    })
        
        return normalized_skills
    
    async def normalize_job_titles(self, job_titles: List[str], fuzzy_threshold: float = 80.0) -> List[Dict[str, str]]:
        """
        Normalize a list of job titles to their canonical forms.
        
        Args:
            job_titles: List of job titles to normalize
            fuzzy_threshold: Minimum similarity score for fuzzy matching
            
        Returns:
            List[Dict[str, str]]: List of normalized job titles with original and canonical forms
        """
        normalized_titles = []
        
        for title in job_titles:
            if not title or not title.strip():
                continue
                
            # Clean the job title
            cleaned_title = self._clean_entity_name(title)
            
            # Try exact normalization first
            canonical_title = await self.ontology_service.normalize_job_title(cleaned_title)
            
            if canonical_title:
                normalized_titles.append({
                    "original": title,
                    "canonical": canonical_title,
                    "confidence": 1.0,
                    "match_type": "exact"
                })
            else:
                # Try fuzzy matching
                fuzzy_match = self._fuzzy_match_job_title(cleaned_title, fuzzy_threshold)
                if fuzzy_match:
                    normalized_titles.append({
                        "original": title,
                        "canonical": fuzzy_match["canonical"],
                        "confidence": fuzzy_match["confidence"],
                        "match_type": "fuzzy"
                    })
                else:
                    # Keep original if no match found
                    normalized_titles.append({
                        "original": title,
                        "canonical": title,
                        "confidence": 0.0,
                        "match_type": "none"
                    })
        
        return normalized_titles
    
    async def normalize_work_experience(self, work_experience: List[Dict]) -> List[Dict]:
        """
        Normalize work experience entries, including job titles and company names.
        
        Args:
            work_experience: List of work experience dictionaries
            
        Returns:
            List[Dict]: Normalized work experience with canonical forms
        """
        normalized_experience = []
        
        for exp in work_experience:
            normalized_exp = exp.copy()
            
            # Normalize job title
            if "title" in exp and exp["title"]:
                title_normalization = await self.normalize_job_titles([exp["title"]])
                if title_normalization:
                    normalized_exp["canonical_title"] = title_normalization[0]["canonical"]
                    normalized_exp["title_confidence"] = title_normalization[0]["confidence"]
                    normalized_exp["title_match_type"] = title_normalization[0]["match_type"]
            
            # Normalize company name (basic cleaning for now)
            if "company" in exp and exp["company"]:
                normalized_exp["canonical_company"] = self._clean_entity_name(exp["company"])
            
            # Normalize skills from responsibilities
            if "responsibilities" in exp and exp["responsibilities"]:
                # Extract skills from responsibilities text
                skills_text = " ".join(exp["responsibilities"])
                extracted_skills = self._extract_skills_from_text(skills_text)
                if extracted_skills:
                    normalized_skills = await self.normalize_skills(extracted_skills)
                    normalized_exp["extracted_skills"] = normalized_skills
            
            normalized_experience.append(normalized_exp)
        
        return normalized_experience
    
    def _clean_entity_name(self, entity_name: str) -> str:
        """
        Clean and normalize an entity name for better matching.
        
        Args:
            entity_name: The entity name to clean
            
        Returns:
            str: Cleaned entity name
        """
        if not entity_name:
            return ""
        
        # Convert to lowercase
        cleaned = entity_name.lower()
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Remove common punctuation that doesn't affect meaning
        cleaned = re.sub(r'[^\w\s-]', '', cleaned)
        
        # Normalize common abbreviations
        abbreviations = {
            "dev": "developer",
            "eng": "engineer",
            "mgr": "manager",
            "admin": "administrator",
            "sys": "system",
            "tech": "technology",
            "info": "information",
            "intl": "international",
            "corp": "corporation",
            "inc": "incorporated",
            "llc": "limited liability company"
        }
        
        for abbr, full in abbreviations.items():
            # Replace standalone abbreviations
            cleaned = re.sub(rf'\b{abbr}\b', full, cleaned)
        
        return cleaned
    
    def _fuzzy_match_skill(self, skill_name: str, threshold: float) -> Optional[Dict]:
        """
        Perform fuzzy matching for a skill name.
        
        Args:
            skill_name: The skill name to match
            threshold: Minimum similarity score
            
        Returns:
            Optional[Dict]: Match result with canonical name and confidence
        """
        try:
            # Get all canonical skills from ontology
            # For now, we'll use a simplified approach
            # In a full implementation, we'd query the ontology for all skills
            
            # This is a placeholder - in practice, we'd get this from the ontology
            common_skills = [
                "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust",
                "React", "Angular", "Vue.js", "Node.js", "Django", "Flask",
                "Docker", "Kubernetes", "AWS", "Azure", "GCP", "MongoDB",
                "PostgreSQL", "MySQL", "Redis", "Elasticsearch", "Kafka",
                "Machine Learning", "Deep Learning", "Data Science",
                "DevOps", "CI/CD", "Git", "Linux", "Agile", "Scrum"
            ]
            
            # Perform fuzzy matching
            best_match = process.extractOne(
                skill_name, 
                common_skills, 
                scorer=fuzz.token_sort_ratio
            )
            
            if best_match and best_match[1] >= threshold:
                return {
                    "canonical": best_match[0],
                    "confidence": best_match[1] / 100.0
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in fuzzy skill matching: {str(e)}")
            return None
    
    def _fuzzy_match_job_title(self, job_title: str, threshold: float) -> Optional[Dict]:
        """
        Perform fuzzy matching for a job title.
        
        Args:
            job_title: The job title to match
            threshold: Minimum similarity score
            
        Returns:
            Optional[Dict]: Match result with canonical name and confidence
        """
        try:
            # Common job titles for matching
            common_titles = [
                "Software Engineer", "Senior Software Engineer", "Full Stack Developer",
                "Frontend Developer", "Backend Developer", "DevOps Engineer",
                "Data Scientist", "Product Manager", "QA Engineer",
                "System Administrator", "Database Administrator", "Network Engineer",
                "Security Engineer", "Cloud Engineer", "Mobile Developer"
            ]
            
            # Perform fuzzy matching
            best_match = process.extractOne(
                job_title, 
                common_titles, 
                scorer=fuzz.token_sort_ratio
            )
            
            if best_match and best_match[1] >= threshold:
                return {
                    "canonical": best_match[0],
                    "confidence": best_match[1] / 100.0
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in fuzzy job title matching: {str(e)}")
            return None
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """
        Extract potential skills from text using keyword matching.
        
        Args:
            text: The text to extract skills from
            
        Returns:
            List[str]: List of potential skills
        """
        # Common technology keywords
        tech_keywords = [
            "python", "javascript", "java", "c++", "c#", "go", "rust",
            "react", "angular", "vue", "node", "django", "flask",
            "docker", "kubernetes", "aws", "azure", "gcp", "mongodb",
            "postgresql", "mysql", "redis", "elasticsearch", "kafka",
            "machine learning", "deep learning", "data science",
            "devops", "ci/cd", "git", "linux", "agile", "scrum"
        ]
        
        extracted_skills = []
        text_lower = text.lower()
        
        for keyword in tech_keywords:
            if keyword in text_lower:
                extracted_skills.append(keyword)
        
        return extracted_skills
    
    def get_normalization_stats(self, normalized_entities: List[Dict]) -> Dict:
        """
        Get statistics about the normalization process.
        
        Args:
            normalized_entities: List of normalized entities
            
        Returns:
            Dict: Statistics about the normalization
        """
        total = len(normalized_entities)
        if total == 0:
            return {
                "total": 0,
                "exact_matches": 0,
                "fuzzy_matches": 0,
                "no_matches": 0,
                "average_confidence": 0.0
            }
        
        exact_matches = sum(1 for e in normalized_entities if e.get("match_type") == "exact")
        fuzzy_matches = sum(1 for e in normalized_entities if e.get("match_type") == "fuzzy")
        no_matches = sum(1 for e in normalized_entities if e.get("match_type") == "none")
        
        total_confidence = sum(e.get("confidence", 0.0) for e in normalized_entities)
        average_confidence = total_confidence / total
        
        return {
            "total": total,
            "exact_matches": exact_matches,
            "fuzzy_matches": fuzzy_matches,
            "no_matches": no_matches,
            "average_confidence": round(average_confidence, 3)
        }
    
    async def add_custom_mapping(self, original: str, canonical: str, entity_type: str = "skill") -> bool:
        """
        Add a custom mapping to the ontology.
        
        Args:
            original: The original entity name
            canonical: The canonical entity name
            entity_type: Type of entity ("skill" or "job_title")
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if entity_type == "skill":
                return await self.ontology_service.add_skill_alias(canonical, original)
            elif entity_type == "job_title":
                return await self.ontology_service.add_job_title_alias(canonical, original)
            else:
                self.logger.error(f"Unknown entity type: {entity_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error adding custom mapping: {str(e)}")
            return False
    
    async def health_check(self) -> bool:
        """
        Perform a health check on the normalization service.
        
        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            return await self.ontology_service.health_check()
        except Exception as e:
            self.logger.error(f"Entity normalization health check failed: {str(e)}")
            return False
    
    def close(self):
        """Close the ontology service connection."""
        self.ontology_service.close() 
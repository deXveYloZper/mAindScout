# app/services/candidate_service.py

import logging
from pymongo.database import Database
from starlette.concurrency import run_in_threadpool
from typing import List, Optional, Dict, Any
from app.schemas.candidate_schema import CandidateProfile
from app.schemas.common import PaginationParams, PaginatedResponse
from app.services.base_service import BaseService
from app.services.vector_service import VectorService
from app.services.candidate_metrics_service import CandidateMetricsService
from app.services.entity_normalization_service import EntityNormalizationService
from app.core.models import CompanyProfile
from app.utils.openai_utils import extract_info_from_text
from app.prompts.candidate_prompts import TECH_CANDIDATE_PROFILE_EXTRACTION_PROMPT
from app.utils import nlp_utils
import os
import json
import re
from sentence_transformers import SentenceTransformer
from fastapi import UploadFile
from app.utils.text_extraction import extract_text_from_file


class CandidateService(BaseService[CandidateProfile]):
    def __init__(
        self,
        db: Database,
        vector_service: VectorService,
        metrics_service: CandidateMetricsService,
        entity_normalization: EntityNormalizationService,
        embedding_model: SentenceTransformer,
        nlp_model
    ):
        super().__init__("CandidateProfiles", db=db)
        self.model = CandidateProfile
        self.vector_service = vector_service
        self.metrics_service = metrics_service
        self.entity_normalization = entity_normalization
        self.embedding_model = embedding_model
        self.logger = logging.getLogger(__name__)
        self.company_collection = db['companies']
        taxonomy_path = os.path.join('app', 'data', 'tag_taxonomy.json')
        with open(taxonomy_path, 'r', encoding='utf-8') as f:
            nested_taxonomy = json.load(f)
        self.flat_taxonomy = nlp_utils.flatten_taxonomy(nested_taxonomy)
        self.nlp_model = nlp_model

    # --- Public CRUD/search API ---
    async def create_candidate(self, candidate: CandidateProfile) -> CandidateProfile:
        """Create a new candidate using the base service."""
        return await self.create(candidate)

    async def get_candidate_by_id(self, candidate_id: str) -> Optional[CandidateProfile]:
        """Get a candidate by ID using the base service."""
        return await self.get_by_id(candidate_id)

    async def get_candidates(
        self,
        pagination: PaginationParams,
        filters: Dict[str, Any],
        sort_by: str,
        sort_order: str
    ) -> PaginatedResponse[CandidateProfile]:
        """Get candidates with pagination and filtering."""
        return await self.get_all(pagination, filters, sort_by, sort_order)

    async def update_candidate(self, candidate_id: str, candidate: CandidateProfile) -> Optional[CandidateProfile]:
        """Update a candidate using the base service."""
        return await self.update(candidate_id, candidate)

    async def delete_candidate(self, candidate_id: str) -> bool:
        """Delete a candidate using the base service."""
        return await self.delete(candidate_id)

    async def search_candidates(
        self,
        query: str,
        pagination: PaginationParams,
        filters: Dict[str, Any] = None
    ) -> PaginatedResponse[CandidateProfile]:
        """Search candidates by text query."""
        search_filters = filters or {}
        search_filters["$text"] = {"$search": query}
        return await self.get_all(pagination, search_filters, "score", "desc")

    async def bulk_create_candidates(self, candidates: List[CandidateProfile]) -> Dict[str, int]:
        """Create multiple candidates in bulk."""
        return await self.bulk_create(candidates)

    async def count_candidates(self, filters: Dict[str, Any] = None) -> int:
        """Count candidates with optional filters."""
        return await self.count(filters)

    async def parse_and_store_candidate_profile(self, resume_text: str) -> CandidateProfile:
        """
        Parse a candidate's profile from extracted resume/CV text using OpenAI, and map it to the CandidateProfile model.
        """
        try:
            # Replace the placeholder with the actual resume/CV text
            prompt = TECH_CANDIDATE_PROFILE_EXTRACTION_PROMPT.replace("[RESUME_TEXT]", resume_text)

            # Extract data using OpenAI
            extracted_data = await run_in_threadpool(extract_info_from_text, resume_text, prompt)

            # Log the extracted data for debugging purposes
            self.logger.debug(f"Extracted Data: {extracted_data}")

            # Map the extracted data to the CandidateProfile model
            mapped_data = {
                "name": extracted_data.get("name"),
                "email": extracted_data.get("email"),
                "phone_number": extracted_data.get("phone_number"),
                "skills": extracted_data.get("skills", []),
                "experience_years": extracted_data.get("experience_years", 0),
                "current_role": extracted_data.get("current_role"),
                "current_company": extracted_data.get("current_company"),
                "desired_role": extracted_data.get("desired_role"),
                "education": extracted_data.get("education", []),
                "certifications": extracted_data.get("certifications", []),
                "languages": [{"language": lang, "proficiency": "unknown"} for lang in extracted_data.get("languages", [])],
                "summary": extracted_data.get("summary"),
                "work_experience": extracted_data.get("work_experience", []),
                "projects": extracted_data.get("projects", []),
                "awards": extracted_data.get("awards", []),
                "location": extracted_data.get("location"),
                "linkedin_url": extracted_data.get("linkedin_url"),
                "github_url": extracted_data.get("github_url"),
                "portfolio_url": extracted_data.get("portfolio_url"),
            }

            # Validate that required fields are present
            if not mapped_data["name"] or not mapped_data["email"]:
                raise ValueError("Required fields 'name' or 'email' are missing in the extracted data.")

            # Enrich work experience by cross-referencing with company profiles
            mapped_data['work_experience'] = await self.enrich_work_experience(mapped_data.get('work_experience', []))

            # Enhance with NLP features
            full_text = resume_text  # Use the entire resume text for NLP processing

            # Extract keywords
            keywords = await run_in_threadpool(nlp_utils.extract_keywords, full_text)
            mapped_data["keywords"] = keywords

            # Extract entities
            entities = await run_in_threadpool(nlp_utils.extract_entities, full_text, self.nlp_model)
            mapped_data["entities"] = entities

            # Classify candidate expertise
            categories = await run_in_threadpool(nlp_utils.classify_candidate, full_text)
            mapped_data["categories"] = categories

            # Standardize skills
            skills = mapped_data.get("skills", [])
            standardized_skills = await run_in_threadpool(nlp_utils.standardize_skills, skills)
            mapped_data["standardized_skills"] = standardized_skills

            # Normalize entities using ontology
            normalized_skills = await self.entity_normalization.normalize_skills(skills)
            mapped_data["normalized_skills"] = normalized_skills
            
            # Normalize work experience
            if mapped_data.get("work_experience"):
                normalized_work_exp = await self.entity_normalization.normalize_work_experience(mapped_data["work_experience"])
                mapped_data["normalized_work_experience"] = normalized_work_exp

            # Generate tags
            tags = await run_in_threadpool(self.generate_candidate_tags, mapped_data)
            mapped_data["tags"] = tags

            # Create CandidateProfile object
            candidate_profile = CandidateProfile(**mapped_data)
            
            # Calculate derived metrics
            metrics = await run_in_threadpool(self.metrics_service.calculate_candidate_metrics, mapped_data)
            mapped_data.update(metrics)
            
            # Update candidate profile with metrics
            candidate_profile = CandidateProfile(**mapped_data)

            # Check if candidate already exists
            existing_candidate = await run_in_threadpool(self.collection.find_one, {"email": candidate_profile.email})
            if existing_candidate:
                # Update the existing candidate record
                final_candidate = await self.update(str(existing_candidate['_id']), candidate_profile)
                self.logger.info(f"Candidate profile updated for email: {final_candidate.email}")
            else:
                # Create a new candidate record
                final_candidate = await self.create(candidate_profile)
                self.logger.info(f"New candidate profile created for email: {final_candidate.email}")

            # Generate and store the vector embedding for the final profile
            if final_candidate:
                candidate_id = str(final_candidate.id)
                await self._generate_and_store_embedding(final_candidate, candidate_id)

            return final_candidate

        except Exception as e:
            # Improved error handling (Point 6)
            self.logger.error(f"Failed to parse and store candidate profile: {str(e)}", exc_info=True)
            raise ValueError(f"Error processing candidate profile: {str(e)}") from e

    async def parse_and_store_candidate_profile_from_file(self, file: UploadFile) -> CandidateProfile:
        """
        Creates a CandidateProfile from an uploaded file.
        """
        try:
            resume_text = await extract_text_from_file(file)
            return await self.parse_and_store_candidate_profile(resume_text)
        except Exception as e:
            self.logger.error(f"Failed to create candidate profile from file: {str(e)}", exc_info=True)
            raise ValueError(f"Error processing candidate profile from file: {str(e)}") from e

    async def get_company_profile_by_name(self, company_name: str) -> Optional[CompanyProfile]:
        """
        Retrieves a company profile by company name from the database.

        Args:
            company_name (str): The name of the company.

        Returns:
            Optional[CompanyProfile]: The company profile if found, otherwise None.
        """
        try:
            company_data = await run_in_threadpool(self.company_collection.find_one, {"company_name": company_name})
            if company_data:
                return CompanyProfile(**company_data)
            else:
                self.logger.debug(f"No company found with name: {company_name}")
                return None
        except Exception as e:
            self.logger.error(f"Error retrieving company with name {company_name}: {str(e)}", exc_info=True)
            return None

    async def enrich_work_experience(self, work_experience: List[dict]) -> List[dict]:
        """
        Enrich the work experience entries with data from the company database.

        Args:
            work_experience (List[dict]): List of work experience dictionaries.

        Returns:
            List[dict]: Enriched list of work experience dictionaries.
        """
        enriched_experience = []

        for experience in work_experience:
            company_name = experience.get("company")
            if company_name:
                company_data = await self.cross_reference_company(company_name)
                if company_data:
                    # Enrich work experience with company data
                    experience['company_type'] = company_data.get('company_type')
                    experience['industry'] = company_data.get('industry', [])
                    experience['tech_stack'] = [tech.technology for tech in company_data.get('tech_stack', [])]

            enriched_experience.append(experience)

        return enriched_experience

    async def cross_reference_company(self, company_name: str) -> Optional[dict]:
        """
        Cross-references a company name with the company database.

        Args:
            company_name (str): The name of the company to look up.

        Returns:
            Optional[dict]: The company data if found, otherwise None.
        """
        try:
            # Perform a case-insensitive search for the company name
            company = await run_in_threadpool(
                self.company_collection.find_one,
                {"company_name": {"$regex": f"^{re.escape(company_name)}$", "$options": "i"}}
            )
            if company:
                return company
            else:
                self.logger.info(f"Company '{company_name}' not found in the database.")
                return None
        except Exception as e:
            self.logger.error(f"Error during company cross-reference: {str(e)}", exc_info=True)
            return None

    def process_projects(self, projects: List[str]) -> List[dict]:
        """
        Convert the project data from list of strings to list of dictionaries.
        """
        processed_projects = []
        for project in projects:
            if isinstance(project, str):
                processed_projects.append({
                    "project_name": project,
                    "description": None,  # Placeholder if more data is needed
                    "start_date": None,
                    "end_date": None,
                    "technologies_used": []
                })
            elif isinstance(project, dict):
                processed_projects.append(project)
        return processed_projects

    def generate_candidate_tags(self, candidate_data: dict) -> List[str]:
        """
        Generate tags for a candidate based on their skills, experience, and other relevant fields.
        """
        text_components = []

        # Include various fields for tagging
        if candidate_data.get("skills"):
            text_components.append(' '.join(candidate_data["skills"]))
        if candidate_data.get("standardized_skills"):
            text_components.append(' '.join(candidate_data["standardized_skills"]))
        if candidate_data.get("summary"):
            text_components.append(candidate_data["summary"])

        # Handle work experience field if it's a list of dictionaries
        if candidate_data.get("work_experience"):
            for experience in candidate_data["work_experience"]:
                if isinstance(experience, dict):
                    # Extract key fields from the work experience dictionary
                    experience_text = ' '.join(str(value) for value in experience.values() if isinstance(value, str))
                    text_components.append(experience_text)
                elif isinstance(experience, str):
                    text_components.append(experience)

        # Handle projects if they are a list of dictionaries
        if candidate_data.get("projects"):
            for project in candidate_data["projects"]:
                if isinstance(project, dict):
                    project_text = ' '.join(str(value) for value in project.values() if isinstance(value, str))
                    text_components.append(project_text)
                elif isinstance(project, str):
                    text_components.append(project)

        if candidate_data.get("education"):
            if isinstance(candidate_data["education"], list):
                education_text = ' '.join(str(edu) for edu in candidate_data["education"] if isinstance(edu, str))
                text_components.append(education_text)

        if candidate_data.get("certifications"):
            if isinstance(candidate_data["certifications"], list):
                certifications_text = ' '.join(str(cert) for cert in candidate_data["certifications"] if isinstance(cert, str))
                text_components.append(certifications_text)

        # Combine all text components into a single string
        combined_text = ' '.join(text_components).lower()

        # Generate tags using the flattened taxonomy
        tags = nlp_utils.generate_company_tags(combined_text, self.flat_taxonomy)
        return tags

    async def _generate_and_store_embedding(self, candidate_profile: CandidateProfile, candidate_id: str) -> bool:
        """
        Generate and store vector embedding for a candidate profile.
        
        Args:
            candidate_profile: The candidate profile object
            candidate_id: The candidate's database ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create text representation for embedding
            text_components = []
            
            # Add name
            if candidate_profile.name:
                text_components.append(candidate_profile.name)
            
            # Add skills
            if candidate_profile.skills:
                text_components.extend(candidate_profile.skills)
            
            # Add summary
            if candidate_profile.summary:
                text_components.append(candidate_profile.summary)
            
            # Add work experience
            if candidate_profile.work_experience:
                for exp in candidate_profile.work_experience:
                    if isinstance(exp, dict):
                        exp_text = ' '.join(str(v) for v in exp.values() if isinstance(v, str))
                        text_components.append(exp_text)
            
            # Add education
            if candidate_profile.education:
                for edu in candidate_profile.education:
                    if isinstance(edu, dict):
                        edu_text = ' '.join(str(v) for v in edu.values() if isinstance(v, str))
                        text_components.append(edu_text)
            
            # Combine all text components
            combined_text = ' '.join(text_components)
            
            # Generate embedding
            embedding = self.embedding_model.encode(combined_text).tolist()
            
            # Prepare metadata
            metadata = {
                "name": candidate_profile.name,
                "email": candidate_profile.email,
                "skills": candidate_profile.skills,
                "experience_years": candidate_profile.experience_years,
                "location": candidate_profile.location
            }
            
            # Store in vector database
            success = await run_in_threadpool(self.vector_service.store_candidate_embedding,
                candidate_id=candidate_id,
                embedding=embedding,
                metadata=metadata
            )
            
            if success:
                self.logger.info(f"Successfully stored embedding for candidate {candidate_id}")
            else:
                self.logger.error(f"Failed to store embedding for candidate {candidate_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error generating embedding for candidate {candidate_id}: {str(e)}")
            return False

    async def get_candidate_embedding(self, candidate_id: str) -> Optional[List[float]]:
        """
        Get the vector embedding for a candidate.
        
        Args:
            candidate_id: The candidate's database ID
            
        Returns:
            Optional[List[float]]: The candidate's embedding if found, None otherwise
        """
        try:
            return await run_in_threadpool(self.vector_service.get_embedding, candidate_id)
        except Exception as e:
            self.logger.error(f"Error getting embedding for candidate {candidate_id}: {str(e)}")
            return None

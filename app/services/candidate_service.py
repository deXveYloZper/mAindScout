# app/services/candidate_service.py

import logging
from app.core.models import CandidateProfile
from app.utils.openai_utils import extract_info_from_text
from app.prompts.candidate_prompts import TECH_CANDIDATE_PROFILE_EXTRACTION_PROMPT
from app.utils import nlp_utils 
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from typing import List, Optional
import os
import json




class CandidateService:
    def __init__(self, db_uri: str, db_name: str):
        self.logger = logging.getLogger(__name__)
        self.client = MongoClient(db_uri)
        self.db = self.client[db_name]
        self.candidate_collection = self.db['CandidateProfiles']

        # Load the taxonomy
        taxonomy_path = os.path.join('app', 'data', 'tag_taxonomy.json')
        with open(taxonomy_path, 'r', encoding='utf-8') as f:
            nested_taxonomy = json.load(f)
        # Flatten the taxonomy
        self.flat_taxonomy = nlp_utils.flatten_taxonomy(nested_taxonomy)

        # Create indexes on frequently queried fields (Point 7)
        self.candidate_collection.create_index("email", unique=True)
        self.candidate_collection.create_index("tags")
        self.candidate_collection.create_index("skills")

    def parse_and_store_candidate_profile(self, resume_text: str) -> CandidateProfile:
        """
        Parse a candidate's profile from extracted resume/CV text using OpenAI, and map it to the CandidateProfile model.
        """
        try:
            # Replace the placeholder with the actual resume/CV text
            prompt = TECH_CANDIDATE_PROFILE_EXTRACTION_PROMPT.replace("[RESUME_TEXT]", resume_text)

            # Extract data using OpenAI
            extracted_data = extract_info_from_text(resume_text, prompt)

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
            
            # Enhance with NLP features
            full_text = resume_text  # Use the entire resume text for NLP processing

            # Extract keywords
            keywords = nlp_utils.extract_keywords(full_text)
            mapped_data["keywords"] = keywords

            # Extract entities
            entities = nlp_utils.extract_entities(full_text)
            mapped_data["entities"] = entities

            # Classify candidate expertise
            categories = nlp_utils.classify_candidate(full_text)
            mapped_data["categories"] = categories

            # Standardize skills
            skills = mapped_data.get("skills", [])
            standardized_skills = nlp_utils.standardize_skills(skills)
            mapped_data["standardized_skills"] = standardized_skills

            # Generate tags
            tags = self.generate_candidate_tags(mapped_data)
            mapped_data["tags"] = tags

            # Create CandidateProfile object
            candidate_profile = CandidateProfile(**mapped_data)

           # Store in the database
            try:
                self.candidate_collection.insert_one(candidate_profile.model_dump(by_alias=True))
            except DuplicateKeyError:
                self.logger.error(f"Candidate with email {mapped_data['email']} already exists.", exc_info=True)
                raise ValueError(f"Candidate with email {mapped_data['email']} already exists.")

            return candidate_profile

        except Exception as e:
            # Improved error handling (Point 6)
            self.logger.error(f"Failed to parse and store candidate profile: {str(e)}", exc_info=True)
            raise ValueError(f"Error processing candidate profile: {str(e)}") from e
        
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


    def get_candidate_profile(self, candidate_id: str) -> Optional[CandidateProfile]:
        """
        Retrieve a candidate profile from the database by ID.
        """
        try:
            candidate_data = self.candidate_collection.find_one({"_id": candidate_id})
            if candidate_data:
                return CandidateProfile(**candidate_data)
            else:
                self.logger.warning(f"No candidate found with ID: {candidate_id}")
                return None
        except Exception as e:
            self.logger.error(f"Error retrieving candidate with ID {candidate_id}: {str(e)}", exc_info=True)
            return None


    def update_candidate_profile(self, candidate_id: str, updates: dict) -> bool:
        """
        Update a candidate profile in the database.
        """
        try:
            result = self.candidate_collection.update_one({"_id": candidate_id}, {"$set": updates})
            if result.modified_count > 0:
                self.logger.info(f"Candidate with ID {candidate_id} successfully updated.")
                return True
            else:
                self.logger.warning(f"No changes made to candidate with ID {candidate_id}.")
                return False
        except Exception as e:
            self.logger.error(f"Error updating candidate with ID {candidate_id}: {str(e)}", exc_info=True)
            return False

# app/services/job_service.py

import logging
from typing import List, Optional, Dict
from app.schemas.job_schema import JobDescription
from app.utils.openai_utils import extract_info_from_text
from app.utils.text_extraction import extract_text_from_file
from app.utils import nlp_utils
from app.prompts.job_prompts import TECH_JOB_DESCRIPTION_EXTRACTION_PROMPT
from app.services.vector_service import VectorService
from pymongo import MongoClient
import os
import json
from bson import ObjectId
from fastapi import UploadFile
from sentence_transformers import SentenceTransformer
from pymongo.database import Database
from starlette.concurrency import run_in_threadpool
from app.services.base_service import BaseService


class JobService(BaseService[JobDescription]):
    def __init__(
        self,
        db: Database,
        vector_service: VectorService,
        embedding_model: SentenceTransformer,
        nlp_model
    ):
        super().__init__("JobDescriptions", db=db)
        self.model = JobDescription
        self.vector_service = vector_service
        self.embedding_model = embedding_model
        self.logger = logging.getLogger(__name__)
        self.nlp_model = nlp_model

        # Load the taxonomy
        taxonomy_path = os.path.join('app', 'data', 'tag_taxonomy.json')
        with open(taxonomy_path, 'r', encoding='utf-8') as f:
            nested_taxonomy = json.load(f)
        # Flatten the taxonomy
        self.flat_taxonomy = nlp_utils.flatten_taxonomy(nested_taxonomy)

        # Create indexes on frequently queried fields
        self.collection.create_index("tags")
        self.collection.create_index("required_skills")
        self.collection.create_index("title")
        self.collection.create_index("company_name")


    async def parse_and_store_job_description(self, job_description_text: str) -> JobDescription:
        """
        Parses job description text, enriches it, and stores it in the database asynchronously.
        """
        try:
            prompt = TECH_JOB_DESCRIPTION_EXTRACTION_PROMPT.replace("[JOB_DESCRIPTION_TEXT]", job_description_text)
            # Make the OpenAI call non-blocking
            extracted_data = await run_in_threadpool(extract_info_from_text, job_description_text, prompt)
            self.logger.debug(f"Extracted Data from JD: {extracted_data}")
            mapped_data = {
                "title": extracted_data.get("title"),
                "company_name": extracted_data.get("company_name"),
                "company_description": extracted_data.get("company_description"),
                "company_industry_focus": extracted_data.get("company_industry_focus", []),
                "company_collaborations": extracted_data.get("company_collaborations", []),
                "location": extracted_data.get("location"),
                "employment_type": extracted_data.get("employment_type"),
                "description": extracted_data.get("description"),
                "responsibilities": extracted_data.get("responsibilities", []),
                "must_have_skills": extracted_data.get("must_have_skills", []),
                "good_to_have_skills": extracted_data.get("good_to_have_skills", []),
                "technologies_and_protocols": extracted_data.get("technologies_and_protocols", []),
                # Combine skills into required_skills
                "required_skills": (extracted_data.get("must_have_skills") or []) + (extracted_data.get("good_to_have_skills") or []),
                "experience_level": extracted_data.get("experience_level"),
                "experience_years": extracted_data.get("experience_years"),
                "qualifications": extracted_data.get("qualifications") or [],
                "company_industry_focus": extracted_data.get("company_industry_focus") or [],
                "company_collaborations": extracted_data.get("company_collaborations") or [],
                "education_level": extracted_data.get("education_level"),
                "salary_and_benefits": extracted_data.get("salary_and_benefits"),
                "additional_requirements": extracted_data.get("additional_requirements"),
                "application_instructions": extracted_data.get("application_instructions"),
                "posting_date": extracted_data.get("posting_date"),
                "closing_date": extracted_data.get("closing_date"),
                "industry": extracted_data.get("industry"),
            }
            # Validate that required fields are present
            if not mapped_data["title"] or not mapped_data["description"]:
                raise ValueError("Required fields 'title' or 'description' are missing in the extracted data.")
            # Enhance with NLP features
            description_text = ' '.join([
                mapped_data.get("description") or "",
                mapped_data.get("company_description") or "",
                ' '.join(mapped_data.get("must_have_skills") or []),
                ' '.join(mapped_data.get("good_to_have_skills") or []),
                ' '.join(mapped_data.get("technologies_and_protocols") or []),
            ])
            keywords = nlp_utils.extract_keywords(description_text)
            mapped_data["keywords"] = keywords
            entities = nlp_utils.extract_entities(description_text, self.nlp_model)
            mapped_data["entities"] = entities
            categories = nlp_utils.classify_job(description_text)
            mapped_data["categories"] = categories
            all_skills = mapped_data.get("must_have_skills", []) + mapped_data.get("good_to_have_skills", [])
            standardized_skills = nlp_utils.standardize_skills(all_skills)
            mapped_data["standardized_skills"] = standardized_skills
            experience_level = extracted_data.get("experience_level")
            if experience_level:
                experience_level = experience_level.lower().replace(' ', '-')
                extracted_data["experience_level"] = experience_level
            tags = self.generate_job_tags(mapped_data)
            mapped_data["tags"] = tags
            # Make the database insertion non-blocking
            result = await run_in_threadpool(self.collection.insert_one, mapped_data)
            job_id = result.inserted_id
            # Generate and store embedding (this should also be async or wrapped)
            await self._generate_and_store_embedding(mapped_data, str(job_id))
            final_doc = await run_in_threadpool(self.collection.find_one, {"_id": job_id})
            return JobDescription(**final_doc)
        except Exception as e:
            self.logger.error(f"Failed to process job description: {str(e)}", exc_info=True)
            raise ValueError(f"Error processing job description: {str(e)}") from e

    async def parse_and_store_job_description_from_file(self, file: UploadFile) -> JobDescription:
        """
        Creates a JobDescription object from an uploaded file asynchronously.
        """
        try:
            job_description_text = await extract_text_from_file(file)
            return await self.parse_and_store_job_description(job_description_text)
        except Exception as e:
            self.logger.error(f"Failed to create job description from file: {str(e)}", exc_info=True)
            raise ValueError(f"Error processing job description from file: {str(e)}") from e

    def generate_job_tags(self, job_data: dict) -> List[str]:
        """
        Generate relevant tags for a job description based on its content.

        This function extracts text from specified fields in the job data,
        generates initial tags using the taxonomy, and then filters and ranks
        the tags based on their relevance to the job description.

        Args:
            job_data (dict): The job data containing various fields.

        Returns:
            List[str]: A list of relevant tags.
        """
        text_components = []
        # Fields to include for tag generation
        fields_to_include = [
            "title",
            "description",
            "must_have_skills",
            "good_to_have_skills",
            "technologies_and_protocols",
            "company_description",
            "company_industry_focus",
            "industry"
        ]

        # Extract text from the specified fields
        for field in fields_to_include:
            value = job_data.get(field)
            if isinstance(value, list):
                text_components.append(' '.join(value))
            elif isinstance(value, str):
                text_components.append(value)

        # Combine all text components into a single string and convert to lowercase
        combined_text = ' '.join(text_components).lower()

        # Generate initial tags using the flattened taxonomy
        initial_tags = nlp_utils.generate_company_tags(combined_text, self.flat_taxonomy)

        # Filter and rank tags based on relevance
        relevant_tags = self.filter_relevant_tags(initial_tags, combined_text)

        return relevant_tags

    def filter_relevant_tags(self, tags: List[str], text: str) -> List[str]:
        """
        Filter and rank tags based on their relevance to the provided text.

        This function calculates a relevance score for each tag based on the
        frequency of its keywords in the text. It then filters out tags below
        a relevance threshold and returns the top tags up to a maximum limit.

        Args:
            tags (List[str]): The initial list of tags generated.
            text (str): The text to compare the tags against.

        Returns:
            List[str]: A list of relevant and ranked tags.
        """
        tag_scores = {}
        for tag in tags:
            # Split the tag into keywords by '>' and strip whitespace
            tag_keywords = [kw.strip().lower() for kw in tag.split('>')]
            # Calculate the score based on keyword frequency in the text
            score = sum(text.count(keyword) for keyword in tag_keywords)
            tag_scores[tag] = score

        # Set a relevance threshold (adjust based on testing)
        relevance_threshold = 1

        # Filter tags that meet or exceed the relevance threshold
        filtered_tags = [tag for tag, score in tag_scores.items() if score >= relevance_threshold]

        # Sort the tags by their scores in descending order
        sorted_tags = sorted(filtered_tags, key=lambda tag: tag_scores[tag], reverse=True)

        # Limit the number of tags to the top N tags
        max_tags = 10
        top_tags = sorted_tags[:max_tags]

        return top_tags

    
    async def get_job_description(self, job_id: str) -> Optional[JobDescription]:
        """
        Retrieve a job description from the database by ID.
        """
        try:
            job_data = await run_in_threadpool(self.collection.find_one, {"_id": job_id})
            if job_data:
                return JobDescription(**job_data)
            else:
                self.logger.warning(f"No job found with ID: {job_id}")
                return None
        except Exception as e:
            self.logger.error(f"Error retrieving job with ID {job_id}: {str(e)}", exc_info=True)
            return None
        
    async def update_job_description(self, job_id: str, updates: dict) -> bool:
        """
        Update a job description in the database.
        """
        try:
            result = await run_in_threadpool(self.collection.update_one, {"_id": job_id}, {"$set": updates})
            if result.modified_count > 0:
                self.logger.info(f"Job with ID {job_id} successfully updated.")
                return True
            else:
                self.logger.warning(f"No changes made to job with ID {job_id}.")
                return False
        except Exception as e:
            self.logger.error(f"Error updating job with ID {job_id}: {str(e)}", exc_info=True)
            return False

    async def delete_job_description(self, job_id: str) -> bool:
        """
        Delete a job description from the database.
        """
        try:
            result = await run_in_threadpool(self.collection.delete_one, {"_id": job_id})
            if result.deleted_count > 0:
                # Also delete the vector embedding
                await run_in_threadpool(self.vector_service.delete_embedding, job_id)
                self.logger.info(f"Job with ID {job_id} successfully deleted.")
                return True
            else:
                self.logger.warning(f"No job found with ID {job_id} to delete.")
                return False
        except Exception as e:
            self.logger.error(f"Error deleting job with ID {job_id}: {str(e)}", exc_info=True)
            return False

    async def _generate_and_store_embedding(self, job_data: dict, job_id: str) -> bool:
        """
        Generate and store vector embedding for a job description.
        
        Args:
            job_data: The job data dictionary
            job_id: The job's database ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create text representation for embedding
            text_components = []
            
            # Add title
            if job_data.get("title"):
                text_components.append(job_data["title"])
            
            # Add description
            if job_data.get("description"):
                text_components.append(job_data["description"])
            
            # Add required skills
            if job_data.get("required_skills"):
                text_components.extend(job_data["required_skills"])
            
            # Add responsibilities
            if job_data.get("responsibilities"):
                text_components.extend(job_data["responsibilities"])
            
            # Add qualifications
            if job_data.get("qualifications"):
                text_components.extend(job_data["qualifications"])
            
            # Add company description
            if job_data.get("company_description"):
                text_components.append(job_data["company_description"])
            
            # Combine all text components
            combined_text = ' '.join(text_components)
            
            # Generate embedding
            embedding = self.embedding_model.encode(combined_text).tolist()
            
            # Prepare metadata
            metadata = {
                "title": job_data.get("title"),
                "company_name": job_data.get("company_name"),
                "location": job_data.get("location"),
                "required_skills": job_data.get("required_skills", []),
                "experience_level": job_data.get("experience_level"),
                "employment_type": job_data.get("employment_type")
            }
            
            # Store in vector database
            success = await run_in_threadpool(self.vector_service.store_job_embedding,
                job_id=job_id,
                embedding=embedding,
                metadata=metadata
            )
            
            if success:
                self.logger.info(f"Successfully stored embedding for job {job_id}")
            else:
                self.logger.error(f"Failed to store embedding for job {job_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error generating embedding for job {job_id}: {str(e)}")
            return False

    async def search_similar_jobs(self, candidate_embedding: List[float], limit: int = 10) -> List[Dict]:
        """
        Search for jobs similar to a candidate's profile using vector similarity.
        
        Args:
            candidate_embedding: Candidate profile embedding
            limit: Maximum number of results to return
            
        Returns:
            List[Dict]: List of similar jobs with scores
        """
        try:
            return await run_in_threadpool(
                self.vector_service.search_similar_jobs,
                candidate_embedding=candidate_embedding,
                limit=limit
            )
        except Exception as e:
            self.logger.error(f"Error searching similar jobs: {str(e)}")
            return []

    async def get_job_embedding(self, job_id: str) -> Optional[List[float]]:
        """
        Retrieve a job's embedding from the vector database.
        
        Args:
            job_id: The job's database ID
            
        Returns:
            Optional[List[float]]: The embedding if found, None otherwise
        """
        try:
            return await run_in_threadpool(self.vector_service.get_embedding, job_id)
        except Exception as e:
            self.logger.error(f"Error retrieving job embedding: {str(e)}")
            return None



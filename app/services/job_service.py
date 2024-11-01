# app/services/job_service.py

import logging
from typing import List, Optional
from app.schemas.job_schema import JobDescription
from app.utils.openai_utils import extract_info_from_text
from app.utils.text_extraction import extract_text_from_file
from app.utils import nlp_utils
from app.prompts.job_prompts import TECH_JOB_DESCRIPTION_EXTRACTION_PROMPT
from pymongo import MongoClient
import os
import json
from bson import ObjectId
from fastapi import UploadFile


class JobService:
    def __init__(self, db_uri: str, db_name: str):
        self.logger = logging.getLogger(__name__)
        self.client = MongoClient(db_uri)
        self.db = self.client[db_name]
        self.job_collection = self.db['JobDescriptions']

        # Load the taxonomy
        taxonomy_path = os.path.join('app', 'data', 'tag_taxonomy.json')
        with open(taxonomy_path, 'r', encoding='utf-8') as f:
            nested_taxonomy = json.load(f)
        # Flatten the taxonomy
        self.flat_taxonomy = nlp_utils.flatten_taxonomy(nested_taxonomy)

        # Create indexes on frequently queried fields
        self.job_collection.create_index("tags")
        self.job_collection.create_index("required_skills")
        self.job_collection.create_index("title")
        self.job_collection.create_index("company_name")


    async def create_job_description_from_file(self, file: UploadFile) -> JobDescription:
        """
        Creates a JobDescription object from an uploaded file.

        Args:
            file (UploadFile): The uploaded file containing the job description.

        Returns:
            JobDescription: The created JobDescription object.
        """
        try:
            # Extract text from the file using your existing utility function
            job_description_text = await extract_text_from_file(file)

            # Proceed to create the job description using the extracted text
            return self.create_job_description(job_description_text)
        except Exception as e:
            self.logger.error(f"Failed to create job description from file: {str(e)}", exc_info=True)
            raise ValueError(f"Error processing job description from file: {str(e)}") from e


    def create_job_description(self, job_description_text: str) -> JobDescription:
        try:
            # Replace the placeholder with the actual job description text
            prompt = TECH_JOB_DESCRIPTION_EXTRACTION_PROMPT.replace("[JOB_DESCRIPTION_TEXT]", job_description_text)


            # Extract data using OpenAI
            extracted_data = extract_info_from_text(job_description_text, prompt)

            # Log the extracted data for debugging purposes
            self.logger.debug(f"Extracted Data: {extracted_data}")

            # Log the extracted data for debugging purposes
            self.logger.debug(f"Extracted Data: {extracted_data}")
            print("Extracted Data:")
            print(json.dumps(extracted_data, indent=4))

            # Map the extracted data to the JobDescription model
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
                "required_skills": extracted_data.get("must_have_skills", []) + extracted_data.get("good_to_have_skills", []),
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
            mapped_data.get("description", ""),
            mapped_data.get("company_description", ""),
            ' '.join(mapped_data.get("must_have_skills", [])),
            ' '.join(mapped_data.get("good_to_have_skills", [])),
            ' '.join(mapped_data.get("technologies_and_protocols", [])),
            ])
            # Extract keywords
            keywords = nlp_utils.extract_keywords(description_text)
            mapped_data["keywords"] = keywords

            # Extract entities
            entities = nlp_utils.extract_entities(description_text)
            mapped_data["entities"] = entities

            # Classify job
            categories = nlp_utils.classify_job(description_text)
            mapped_data["categories"] = categories

            # Standardize skills
            all_skills = mapped_data.get("must_have_skills", []) + mapped_data.get("good_to_have_skills", [])
            standardized_skills = nlp_utils.standardize_skills(all_skills)
            mapped_data["standardized_skills"] = standardized_skills

            # After extracting data
            experience_level = extracted_data.get("experience_level")
            if experience_level:
                experience_level = experience_level.lower().replace(' ', '-')
                extracted_data["experience_level"] = experience_level


            # Generate tags
            tags = self.generate_job_tags(mapped_data)
            mapped_data["tags"] = tags

           # Store in the database and capture the result
            result = self.job_collection.insert_one(mapped_data)

           # Now create the JobDescription object with the _id  
            mapped_data['_id'] = ObjectId(str(result.inserted_id))
            job_description = JobDescription(**mapped_data)

            return job_description

        except Exception as e:
            self.logger.error(f"Failed to create job description: {str(e)}", exc_info=True)
            raise ValueError(f"Error processing job description: {str(e)}") from e

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

    
    def get_job_description(self, job_id: str) -> Optional[JobDescription]:
        """
        Retrieve a job description from the database by ID.
        """
        try:
            job_data = self.job_collection.find_one({"_id": job_id})
            if job_data:
                return JobDescription(**job_data)
            else:
                self.logger.warning(f"No job found with ID: {job_id}")
                return None
        except Exception as e:
            self.logger.error(f"Error retrieving job with ID {job_id}: {str(e)}", exc_info=True)
            return None
        
    def update_job_description(self, job_id: str, updates: dict) -> bool:
        """
        Update a job description in the database.
        """
        try:
            result = self.job_collection.update_one({"_id": job_id}, {"$set": updates})
            if result.modified_count > 0:
                self.logger.info(f"Job with ID {job_id} successfully updated.")
                return True
            else:
                self.logger.warning(f"No changes made to job with ID {job_id}.")
                return False
        except Exception as e:
            self.logger.error(f"Error updating job with ID {job_id}: {str(e)}", exc_info=True)
            return False

    def delete_job_description(self, job_id: str) -> bool:
        """
        Delete a job description from the database.
        """
        try:
            result = self.job_collection.delete_one({"_id": job_id})
            if result.deleted_count > 0:
                self.logger.info(f"Job with ID {job_id} successfully deleted.")
                return True
            else:
                self.logger.warning(f"No job found with ID {job_id} to delete.")
                return False
        except Exception as e:
            self.logger.error(f"Error deleting job with ID {job_id}: {str(e)}", exc_info=True)
            return False



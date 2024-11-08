# app/services/company_enrichment_service.py

import logging
import re
from typing import Optional, Dict, List
from pymongo import MongoClient, UpdateOne
from app.core.models import CompanyProfile
from app.utils.web_scraper_utils import WebScraperUtil  # Importing web scraping utility
from datetime import datetime

class CompanyEnrichmentService:
    def __init__(self, db_uri: str, db_name: str):
        """
        Initializes the CompanyEnrichmentService with MongoDB connection details.

        Args:
            db_uri (str): MongoDB connection string.
            db_name (str): Name of the MongoDB database.
        """
        self.logger = logging.getLogger(__name__)
        self.client = MongoClient(db_uri)
        self.db = self.client[db_name]
        self.company_collection = self.db['companies']
        self.provenance_collection = self.db['company_provenance']  # New collection for storing provenance logs
        self.scraper = WebScraperUtil()  # Initialize web scraper utility for enrichment

    def enrich_company_from_candidate(self, candidate_data: Dict) -> None:
        """
        Enrich company profiles based on candidate profile data.

        Args:
            candidate_data (dict): A dictionary representing a candidate profile.
        """
        try:
            work_experiences = candidate_data.get('work_experience', [])
            bulk_operations = []

            for experience in work_experiences:
                company_name = experience.get('company')
                if company_name:
                    # Attempt to find the company in the company collection
                    company = self.company_collection.find_one({"company_name": {"$regex": f"^{re.escape(company_name)}$", "$options": "i"}})

                    if company:
                        # Prepare the fields to be enriched based on the candidate data
                        update_fields = self._prepare_enrichment_fields(company, experience)
                        if update_fields:
                            bulk_operations.append(
                                UpdateOne(
                                    {"_id": company["_id"]},
                                    {"$set": update_fields}
                                )
                            )
                            self._log_provenance(company["_id"], update_fields, candidate_data["_id"])

            if bulk_operations:
                # Execute bulk write to update company profiles
                self.company_collection.bulk_write(bulk_operations)
                self.logger.info(f"Enriched {len(bulk_operations)} companies based on candidate data.")
            else:
                self.logger.info("No companies needed enrichment based on the candidate data.")

        except Exception as e:
            self.logger.error(f"Error during company enrichment from candidate profiles: {str(e)}", exc_info=True)

    def _prepare_enrichment_fields(self, company: dict, work_experience: dict) -> dict:
        """
        Prepares the fields for enrichment based on candidate work experience.

        Args:
            company (dict): The existing company profile.
            work_experience (dict): A candidate's work experience entry.

        Returns:
            dict: Fields to be updated in the company profile.
        """
        update_fields = {}

        # Example enrichment logic
        if "tech_stack" in work_experience:
            existing_tech_stack = {tech.technology for tech in company.get("tech_stack", [])}
            new_tech_stack = set(work_experience.get("tech_stack", []))
            # Add technologies not present in the existing tech stack
            if new_tech_stack - existing_tech_stack:
                update_fields["tech_stack"] = list(existing_tech_stack | new_tech_stack)

        if "industry" in work_experience:
            existing_industries = set(company.get("industry", []))
            new_industries = set(work_experience.get("industry", []))
            # Add industries not present in the existing industries list
            if new_industries - existing_industries:
                update_fields["industry"] = list(existing_industries | new_industries)

        if "location" in work_experience:
            existing_locations = set(company.get("location", []))
            new_locations = {work_experience["location"]}
            if new_locations - existing_locations:
                update_fields["location"] = list(existing_locations | new_locations)

        if "company_type" in work_experience and not company.get("company_type"):
            update_fields["company_type"] = work_experience["company_type"]

        return update_fields

    def _log_provenance(self, company_id: str, update_fields: dict, candidate_id: str):
        """
        Logs the provenance for each update in the company profile.

        Args:
            company_id (str): ID of the company being updated.
            update_fields (dict): Fields that were updated in the company profile.
            candidate_id (str): The ID of the candidate whose data was used for enrichment.
        """
        try:
            provenance_entry = {
                "company_id": company_id,
                "updated_fields": update_fields,
                "source_candidate_id": candidate_id,
                "timestamp": datetime.utcnow()
            }
            self.provenance_collection.insert_one(provenance_entry)
            self.logger.info(f"Provenance logged for company_id {company_id} from candidate_id {candidate_id}.")
        except Exception as e:
            self.logger.error(f"Error logging provenance for company_id {company_id}: {str(e)}", exc_info=True)

    def enrich_company_from_external_sources(self, company_name: str) -> None:
        """
        Enrich company profiles using external sources such as scraping and third-party APIs.

        Args:
            company_name (str): Name of the company to be enriched.
        """
        try:
            company = self.company_collection.find_one({"company_name": {"$regex": f"^{re.escape(company_name)}$", "$options": "i"}})

            if not company:
                self.logger.info(f"Company '{company_name}' not found in the database for external enrichment.")
                return

            # Web scraping to enrich company details
            scraped_data = self.scraper.scrape_company_details(company_name)

            update_fields = {}
            if "description" in scraped_data and not company.get("company_description"):
                update_fields["company_description"] = scraped_data["description"]

            if "industry" in scraped_data:
                existing_industries = set(company.get("industry", []))
                new_industries = set(scraped_data["industry"])
                if new_industries - existing_industries:
                    update_fields["industry"] = list(existing_industries | new_industries)

            if "location" in scraped_data:
                existing_locations = set(company.get("location", []))
                new_locations = set(scraped_data["location"])
                if new_locations - existing_locations:
                    update_fields["location"] = list(existing_locations | new_locations)

            if "tech_stack" in scraped_data:
                existing_tech_stack = {tech.technology for tech in company.get("tech_stack", [])}
                new_tech_stack = set(scraped_data["tech_stack"])
                if new_tech_stack - existing_tech_stack:
                    update_fields["tech_stack"] = list(existing_tech_stack | new_tech_stack)

            if update_fields:
                self.company_collection.update_one({"_id": company["_id"]}, {"$set": update_fields})
                self._log_provenance(company["_id"], update_fields, "external_scraper")
                self.logger.info(f"Company '{company_name}' enriched using external data.")
            else:
                self.logger.info(f"Company '{company_name}' did not need enrichment from external sources.")

        except Exception as e:
            self.logger.error(f"Error during external enrichment for company '{company_name}': {str(e)}", exc_info=True)


# app/services/company_enrichment_service.py

import logging
import re
from typing import Optional, Dict, List
from pymongo import MongoClient, UpdateOne
from pymongo.database import Database
from app.core.models import CompanyProfile
from app.utils.web_scraper_utils import WebScraperUtil  # Importing web scraping utility
from datetime import datetime
from starlette.concurrency import run_in_threadpool

class CompanyEnrichmentService:
    def __init__(self, db: Database, scraper: WebScraperUtil):
        """
        Initializes the CompanyEnrichmentService with MongoDB connection details and scraper utility.

        Args:
            db (Database): MongoDB database object.
            scraper (WebScraperUtil): Web scraper utility instance.
        """
        self.logger = logging.getLogger(__name__)
        self.db = db
        self.company_collection = self.db['companies']
        self.provenance_collection = self.db['company_provenance']  # New collection for storing provenance logs
        self.scraper = scraper  # Use injected web scraper utility

    async def enrich_company_from_candidate(self, candidate_data: Dict) -> None:
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
                    company = await run_in_threadpool(self.company_collection.find_one, {"company_name": {"$regex": f"^{re.escape(company_name)}$", "$options": "i"}})

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
                            await run_in_threadpool(self._log_provenance, company["_id"], update_fields, candidate_data["_id"])

            if bulk_operations:
                # Execute bulk write to update company profiles
                await run_in_threadpool(self.company_collection.bulk_write, bulk_operations)
                self.logger.info(f"Enriched {len(bulk_operations)} companies based on candidate data.")
            else:
                self.logger.info("No companies needed enrichment based on the candidate data.")

        except Exception as e:
            self.logger.error(f"Error during company enrichment from candidate profiles: {str(e)}", exc_info=True)

    async def enrich_company_from_external_sources(self, company_name: str) -> None:
        """
        Enrich company profiles using external sources such as scraping via ScrapeGraphAI.

        Args:
            company_name (str): Name of the company to be enriched.
        """
        try:
            company = await run_in_threadpool(self.company_collection.find_one, {"company_name": {"$regex": f"^{re.escape(company_name)}$", "$options": "i"}})

            if not company:
                self.logger.info(f"Company '{company_name}' not found in the database for external enrichment.")
                return

            # Use ScrapeGraphAI to scrape company details
            scraped_data = await self.scraper.scrape_company_details(f"https://{company_name}.com")

            update_fields = {}
            if "description" in scraped_data and not company.get("company_description"):
                update_fields["company_description"] = scraped_data["description"]

            if "industry" in scraped_data:
                existing_industries = set(company.get("industry", []))
                new_industries = set(scraped_data["industry"].split(", ")) if scraped_data.get("industry") else set()
                if new_industries - existing_industries:
                    update_fields["industry"] = list(existing_industries | new_industries)

            if "location" in scraped_data:
                existing_locations = set(company.get("location", []))
                new_locations = set(scraped_data["location"].split(", ")) if scraped_data.get("location") else set()
                if new_locations - existing_locations:
                    update_fields["location"] = list(existing_locations | new_locations)

            if "tech_stack" in scraped_data:
                existing_tech_stack = {tech.technology for tech in company.get("tech_stack", [])}
                new_tech_stack = set(scraped_data["tech_stack"])
                if new_tech_stack - existing_tech_stack:
                    update_fields["tech_stack"] = list(existing_tech_stack | new_tech_stack)

            if update_fields:
                await run_in_threadpool(self.company_collection.update_one, {"_id": company["_id"]}, {"$set": update_fields})
                await run_in_threadpool(self._log_provenance, company["_id"], update_fields, "external_scraper")
                self.logger.info(f"Company '{company_name}' enriched using external data.")
            else:
                self.logger.info(f"Company '{company_name}' did not need enrichment from external sources.")

        except Exception as e:
            self.logger.error(f"Error during external enrichment for company '{company_name}': {str(e)}", exc_info=True)

    def _log_provenance(self, company_id: str, update_fields: dict, source: str):
        """
        Logs the provenance for each update in the company profile.

        Args:
            company_id (str): ID of the company being updated.
            update_fields (dict): Fields that were updated in the company profile.
            source (str): The source of the enrichment (e.g., candidate or scraper).
        """
        try:
            provenance_entry = {
                "company_id": company_id,
                "updated_fields": update_fields,
                "source": source,
                "timestamp": datetime.utcnow()
            }
            self.provenance_collection.insert_one(provenance_entry)
            self.logger.info(f"Provenance logged for company_id {company_id} from source {source}.")
        except Exception as e:
            self.logger.error(f"Error logging provenance for company_id {company_id}: {str(e)}", exc_info=True)

    def _prepare_enrichment_fields(self, company: Dict, experience: Dict) -> Dict:
        """
        Prepare fields to be enriched based on candidate work experience.
        
        Args:
            company (Dict): Current company data from database
            experience (Dict): Work experience data from candidate
            
        Returns:
            Dict: Fields to be updated in the company profile
        """
        update_fields = {}
        
        # Enrich company description if not present
        if not company.get("company_description") and experience.get("description"):
            update_fields["company_description"] = experience["description"]
        
        # Enrich industry information
        if experience.get("industry"):
            existing_industries = set(company.get("industry", []))
            new_industry = experience["industry"]
            if new_industry not in existing_industries:
                update_fields["industry"] = list(existing_industries | {new_industry})
        
        # Enrich location information
        if experience.get("location"):
            existing_locations = set(company.get("location", []))
            new_location = experience["location"]
            if new_location not in existing_locations:
                update_fields["location"] = list(existing_locations | {new_location})
        
        # Enrich tech stack information
        if experience.get("technologies_used"):
            existing_tech_stack = {tech.technology for tech in company.get("tech_stack", [])}
            new_technologies = set(experience["technologies_used"])
            if new_technologies - existing_tech_stack:
                # Convert to TechStackItem format
                new_tech_items = [{"technology": tech, "type": None, "level": None} 
                                for tech in new_technologies - existing_tech_stack]
                update_fields["tech_stack"] = list(company.get("tech_stack", [])) + new_tech_items
        
        return update_fields

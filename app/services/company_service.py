# app/services/company_service.py

import logging
from pymongo.database import Database
from starlette.concurrency import run_in_threadpool
from typing import List, Optional, Dict
from app.schemas.company_schema import CompanyProfile
from app.services.base_service import BaseService
import pandas as pd
import numpy as np
import json
from datetime import datetime
import os
from app.utils.nlp_utils import generate_company_tags, flatten_taxonomy

class CompanyService(BaseService[CompanyProfile]):
    def __init__(self, db: Database):
        super().__init__("companies", db=db)
        self.model = CompanyProfile
        self.logger = logging.getLogger(__name__)
          # Load the taxonomy
        taxonomy_path = os.path.join('app', 'data', 'tag_taxonomy.json')
        with open(taxonomy_path, 'r', encoding='utf-8') as f:
            nested_taxonomy = json.load(f)
        # Flatten the taxonomy
        self.flat_taxonomy = flatten_taxonomy(nested_taxonomy)
        # Create an index on tags for efficient querying
        self.collection.create_index("tags")

    async def parse_and_store_company_profiles_from_json(self, json_file_path: str, batch_size: int = 1000):
        """
        Parse company profiles from a JSON file and store them in the database in batches.
        """
        try:
            with open(json_file_path, 'r', encoding='utf-8') as json_file:
                records = json.load(json_file)

            total_records = len(records)
            self.logger.info(f"Total records to process: {total_records}")

            for i in range(0, total_records, batch_size):
                batch_records = records[i:i + batch_size]
                company_profiles = []
                for record in batch_records:
                    try:
                        company_profile = self.map_record_to_company_profile(record)
                        if company_profile:
                         company_profiles.append(company_profile.model_dump(by_alias=True))
                    except Exception as e:
                        self.logger.error(f"Error processing record with id {record.get('id', 'Unknown')}: {str(e)}", exc_info=True)
                if company_profiles:
                    await run_in_threadpool(self.collection.insert_many, company_profiles)
                self.logger.info(f"Processed batch {i // batch_size + 1} / {total_records // batch_size + 1}")

        except Exception as e:
            self.logger.error(f"An error occurred while parsing company profiles: {str(e)}")

    def map_record_to_company_profile(self, record) -> Optional[CompanyProfile]:
            try:
                mapped_data = {
                    "_id": record['id'],
                    "created_at": self.parse_date(record.get('created_at')),
                    "company_name": record['name'],
                    "company_description": record.get('short_description') or "",
                    "industry": self.process_categories(record.get('categories')),
                    "website": record.get('website'),
                    "location": self.process_locations(record.get('locations')),
                    "company_type": record.get('company_type'),
                    "operating_status": record.get('operating_status'),
                    "company_size": self.decode_employee_count(record.get('num_employees_enum')),
                    "founded_on": self.parse_date(record.get('founded_on')),
                    "semrush_global_rank": record.get('semrush_global_rank'),
                    "semrush_visits_latest_month": record.get('semrush_visits_latest_month'),
                    "num_investors": self.safe_int(record.get('num_investors')),
                    "funding_total": self.safe_float(record.get('funding_total')),
                    "num_exits": self.safe_int(record.get('num_exits')),
                    "num_funding_rounds": self.safe_int(record.get('num_funding_rounds')),
                    "last_funding_type": record.get('last_funding_type'),
                    "last_funding_at": self.parse_date(record.get('last_funding_at')),
                    "num_acquisitions": self.safe_int(record.get('num_acquisitions')),
                    "apptopia_total_apps": self.safe_int(record.get('apptopia_total_apps')),
                    "apptopia_total_downloads": self.safe_int(record.get('apptopia_total_downloads')),
                    "contact_email": record.get('contact_email'),
                    "phone_number": record.get('phone_number'),
                    "facebook": record.get('facebook'),
                    "linkedin": record.get('linkedin'),
                    "twitter": record.get('twitter'),
                    "num_investments": self.safe_int(record.get('num_investments')),
                    "num_lead_investments": self.safe_int(record.get('num_lead_investments')),
                    "num_lead_investors": self.safe_int(record.get('num_lead_investors')),
                    "listed_stock_symbol": record.get('listed_stock_symbol'),
                    "hub_tags": self.process_comma_separated_field(record.get('hub_tags')),
                    "ipo_status": record.get('ipo_status'),
                    "growth_insight_description": record.get('growth_insight_description'),
                    "growth_insight_indicator": record.get('growth_insight_indicator'),
                    "growth_insight_direction": record.get('growth_insight_direction'),
                    "growth_insight_confidence": record.get('growth_insight_confidence'),
                    "investor_insight_description": record.get('investor_insight_description'),
                    "permalink": record.get('permalink'),
                    "url": record.get('url'),
                    "founders": self.process_comma_separated_field(record.get('founders')),
                    # Process additional fields as needed
                }

                # Create CompanyProfile object
                company_profile = CompanyProfile(**mapped_data)

                # Generate tags using the tagging service
                tags = self.generate_company_tags(company_profile)
                company_profile.tags = tags
                return company_profile

            except Exception as e:
                self.logger.error(f"Error mapping record with id {record.get('id', 'Unknown')}: {str(e)}")
                return None  # Skip the record if it can't be processed



    def process_categories(self, categories_str: Optional[str]) -> List[str]:
        """
        Split the categories string into a list and standardize the industry names.
        """
        if categories_str:
            categories = [cat.strip() for cat in categories_str.split(',')]
            return categories
        else:
            return []


    def process_locations(self, locations_str: Optional[str]) -> Optional[str]:
        """
        Process the locations string to extract the primary location.
        """
        if locations_str:
            locations = [loc.strip() for loc in locations_str.split(',')]
            # Choose the most relevant location
            # For example, select the first specific location that's not a region
            for loc in locations:
                if loc and not any(keyword in loc.lower() for keyword in ['middle east', 'africa', 'europe', 'asia', 'americas']):
                    return loc
            # If no specific location is found, return the first one
            return locations[0] if locations else None
        else:
            return None
        
    def decode_employee_count(self, employee_enum: Optional[str]) -> Optional[str]:
        """
        Decode the employee count enum to a meaningful company size.
        """
        employee_ranges = {
            'c_00001_00010': '1-10 employees',
            'c_00011_00050': '11-50 employees',
            'c_00051_00100': '51-100 employees',
            'c_00101_00250': '101-250 employees',
            'c_00251_00500': '251-500 employees',
            'c_00501_001000': '501-1,000 employees',
            'c_01001_005000': '1,001-5,000 employees',
            'c_05001_010000': '5,001-10,000 employees',
            'c_10001_max': '10,001+ employees',
        }
        if employee_enum:
            return employee_ranges.get(employee_enum, 'Unknown')
        else:
            return 'Unknown'
        
    def parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        if date_str:
            try:
                return datetime.fromisoformat(date_str)
            except ValueError:
                self.logger.warning(f"Invalid date format: {date_str}")
                return None
        return None

    def safe_int(self, value) -> Optional[int]:
        try:
            return int(value) if value is not None else None
        except (ValueError, TypeError):
            return None

    def safe_float(self, value) -> Optional[float]:
        try:
            return float(value) if value is not None else None
        except (ValueError, TypeError):
            return None

    def process_comma_separated_field(self, field_value: Optional[str]) -> List[str]:
        if field_value:
            return [item.strip() for item in field_value.split(',') if item.strip()]
        return []



    async def get_company_profile(self, company_id: str) -> Optional[CompanyProfile]:
        """
        Retrieve a company profile from the database by ID.
        """
        company_data = await run_in_threadpool(self.collection.find_one, {"_id": company_id})
        if company_data:
            return CompanyProfile(**company_data)
        else:
            return None
        

    def generate_company_tags(self, company_profile: CompanyProfile) -> List[str]:
        """
        Generate tags for a company based on its description and additional fields.
        """
        description = company_profile.company_description or ''
        industry = ' '.join(company_profile.industry)
        combined_text = f"{description} {industry}"
        tags = generate_company_tags(combined_text, self.flat_taxonomy)
        return tags


    # Additional methods for querying and updating company profiles can be added here

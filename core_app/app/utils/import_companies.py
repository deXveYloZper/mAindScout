# app/utils/import_companies.py

"""
This script processes company data from CSV files and imports it into a MongoDB database using Beanie.
It includes data validation, type conversion, and indexing to optimize query performance.
"""

import sys
import os

# Add the project root directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Optional
from pydantic import ValidationError
import urllib.parse
import re
import asyncio
import unicodedata

# Import the Beanie model
from app.core.models import CompanyProfile  # Adjust the import path as needed

# Import the custom logger
from app.core.logging import logger

# Import Beanie and Motor
from beanie import init_beanie
import motor.motor_asyncio

# Import email_validator for email validation
from email_validator import validate_email, EmailNotValidError

BATCH_SIZE = 5000  # Reduced batch size for better performance

class CompanyImporter:
    def __init__(self, db_uri: str, db_name: str):
        """
        Initializes the CompanyImporter with MongoDB connection details.
        """
        self.logger = logger  # Use the custom logger from logging.py
        self.db_uri = db_uri
        self.db_name = db_name

    async def import_companies(self, csv_file_path: str, max_entries: Optional[int] = None):
        """
        Imports company data from a CSV file into MongoDB using Beanie.
        """
        # Initialize Beanie and MongoDB connection
        await self.init_db()

        self.logger.info(f"Processing file: {csv_file_path}")
        try:
            # Read CSV file into DataFrame
            df = pd.read_csv(csv_file_path)

            # If max_entries is set, limit the DataFrame
            if max_entries:
                df = df.head(max_entries)

            # Data cleaning and type conversion
            df = self.preprocess_dataframe(df)

            # Convert DataFrame to list of records
            records = df.to_dict(orient='records')

            # Process in batches
            total_records = len(records)
            for start_idx in range(0, total_records, BATCH_SIZE):
                end_idx = min(start_idx + BATCH_SIZE, total_records)
                batch = records[start_idx:end_idx]
                self.logger.info(f"Processing records {start_idx} to {end_idx}")

                # Validate and insert records
                validated_records = self.validate_records(batch)

                if validated_records:
                    # Insert records into MongoDB using Beanie with retry logic
                    await self.insert_records(validated_records, start_idx, end_idx)
                else:
                    self.logger.warning(f"No valid records found in records {start_idx} to {end_idx}")

        except Exception as e:
            self.logger.error(f"An error occurred while processing {csv_file_path}: {str(e)}")

        self.logger.info("Data import completed.")

    async def init_db(self):
        client = motor.motor_asyncio.AsyncIOMotorClient(self.db_uri)
        await init_beanie(database=client[self.db_name], document_models=[CompanyProfile])

    def preprocess_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocesses the DataFrame by handling missing values and converting data types.
        """
        # Replace NaN with None
        df = df.astype(object).where(pd.notnull(df), None)

        # Normalize text fields to remove special characters
        text_fields = ['name', 'short_description', 'permalink']
        for field in text_fields:
            df[field] = df[field].apply(self.normalize_text)

        # Convert date fields to datetime and replace NaT with None
        date_fields = ['created_at', 'last_funding_at', 'founded_on']
        for field in date_fields:
            df[field] = pd.to_datetime(df[field], errors='coerce')
            df[field] = df[field].where(df[field].notnull(), None)

        # Convert numeric fields
        numeric_fields = [
            'semrush_global_rank', 'semrush_visits_latest_month',
            'funding_total', 'num_investors', 'num_exits',
            'num_funding_rounds', 'num_acquisitions', 'apptopia_total_apps',
            'apptopia_total_downloads', 'num_investments', 'num_lead_investments',
            'num_lead_investors'
        ]
        for field in numeric_fields:
            df[field] = pd.to_numeric(df[field], errors='coerce')

        # Split string fields into lists
        list_fields = ['categories', 'founders', 'hub_tags', 'locations']
        for field in list_fields:
            df[field] = df[field].apply(lambda x: x.split(', ') if x and isinstance(x, str) else [])

        # Clean and normalize URLs
        url_fields = ['website', 'facebook', 'linkedin', 'twitter', 'url']
        for field in url_fields:
            df[field] = df[field].apply(self.clean_url)

        # Clean and validate email addresses
        df['contact_email'] = df['contact_email'].apply(self.clean_email)

        # Map CSV columns to Pydantic model fields
        df.rename(columns={
            'id': 'id',  # Beanie uses 'id' instead of '_id'
            'name': 'company_name',
            'short_description': 'company_description',
            'categories': 'industry',
            'locations': 'location',  # Now a list of strings
            'num_employees_enum': 'company_size'
        }, inplace=True)

        # Additional fields for future use
        additional_list_fields = ['tech_stack', 'company_culture', 'values', 'domain_expertise', 'tags']
        for field in additional_list_fields:
            if field in df.columns:
                df[field] = df[field].apply(lambda x: x if isinstance(x, list) else [])
            else:
                df[field] = [[]] * len(df)

        # Preprocess tech_stack
        df['tech_stack'] = df['tech_stack'].apply(self.preprocess_tech_stack)

        # Preprocess domain_expertise
        df['domain_expertise'] = df['domain_expertise'].apply(self.preprocess_domain_expertise)

        # Preprocess growth_timeline
        df['growth_timeline'] = df.apply(self.preprocess_growth_timeline, axis=1)

        # Replace any remaining NaN values with None
        df = df.astype(object).where(pd.notnull(df), None)

        return df

    def normalize_text(self, text):
        """
        Normalizes text by removing special characters.
        """
        if text:
            text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
            text = re.sub(r'[^\x00-\x7F]+', '', text)  # Remove non-ASCII characters
            return text
        return text

    def clean_url(self, url: Optional[str]) -> Optional[str]:
        """
        Cleans and normalizes URLs by decoding percent-encoded characters and removing special characters.
        """
        if not url:
            return None

        # Split if multiple URLs are in one string
        urls = re.split(r'[;, \n]+', url)
        cleaned_urls = []

        for url in urls:
            url = url.strip()
            if not url:
                continue

            # Remove unwanted prefixes
            url = re.sub(r'^(https?:\/\/)+', '', url, flags=re.IGNORECASE)
            url = url.lstrip(':/')

            # Decode percent-encoded characters
            url = urllib.parse.unquote(url)

            # Normalize Unicode characters to ASCII equivalents
            url = unicodedata.normalize('NFKD', url).encode('ASCII', 'ignore').decode('utf-8')

            # Remove any remaining non-ASCII characters
            url = re.sub(r'[^\x00-\x7F]+', '', url)

            # Remove whitespace
            url = url.strip()

            # Fix common issues with the protocol part
            # If URL starts with 'httphttp' or 'httpshttps', fix it
            url = re.sub(r'^(https?)(https?):', r'\1:', url, flags=re.IGNORECASE)
            url = re.sub(r'^(https?):+', r'\1://', url, flags=re.IGNORECASE)

            # Remove duplicate 'http://' or 'https://' in the URL
            url = re.sub(r'^(https?:\/\/)(https?:\/\/)+', r'\1', url, flags=re.IGNORECASE)

            # If URL doesn't start with http:// or https://, prepend http://
            if not re.match(r'^https?://', url, re.IGNORECASE):
                url = 'http://' + url

            # Validate the URL
            try:
                result = urllib.parse.urlparse(url)
                if all([result.scheme, result.netloc]):
                    cleaned_urls.append(url)
                else:
                    self.logger.warning(f"Invalid URL '{url}': Missing scheme or netloc")
            except Exception as e:
                self.logger.warning(f"Invalid URL '{url}': {e}")
                continue

        return cleaned_urls[0] if cleaned_urls else None  # Return the first valid URL

    def clean_email(self, email: Optional[str]) -> Optional[str]:
        """
        Cleans and validates email addresses.
        """
        if not email:
            return None

        # Handle multiple emails in one string
        emails = re.split(r'[;, \n/|]+', email)
        for email in emails:
            email = email.strip()
            if not email:
                continue

            # Remove unwanted prefixes and suffixes
            email = re.sub(r'^(mailto:|maito:|email:|E:|e:|\[at\]|[\(\[]+)', '', email, flags=re.IGNORECASE)
            email = email.strip('\'"<>():[]/')

            # Remove any unsafe characters
            email = ''.join(c for c in email if c.isprintable())

            # Remove invisible characters
            email = re.sub(r'[\u200b\u200c\u200d\u200e\u200f\u202a-\u202e\u2060-\u206f\ufeff\ufeff\uf0b7]', '', email)

            # Replace common typos and encoding issues
            email = email.replace('@@', '@').replace('(@)', '@').replace('(at)', '@').replace('[at]', '@').replace('{at}', '@')
            email = email.replace('%20', '').replace('=', '').replace('–', '-').replace('‐', '-').replace('‒', '-')
            email = email.replace('…', '...').replace('‘', "'").replace('’', "'").replace('“', '"').replace('”', '"')
            email = email.replace('\xad', '').replace('\u200b', '').replace('\u200d', '')

            # Remove any trailing periods or commas
            email = email.rstrip('.,')

            # Remove any leading or trailing non-word characters
            email = re.sub(r'^\W+|\W+$', '', email)

            # Remove any text after unintended characters
            email = re.split(r'[\s,/]+', email)[0]

            try:
                # Validate and normalize the email
                valid = validate_email(email, check_deliverability=False)
                email = valid.email
                return email  # Return the first valid email
            except EmailNotValidError as e:
                self.logger.warning(f"Invalid email '{email}': {e}")
                continue

        return None  # Return None if no valid email found

    def preprocess_tech_stack(self, tech_stack_list):
        """
        Preprocesses the tech_stack field to structure the data.
        """
        tech_items = []
        if tech_stack_list:
            for tech in tech_stack_list:
                tech_item = {
                    'technology': tech,
                    'type': self.infer_tech_type(tech),
                    'level': self.infer_tech_level(tech),
                }
                tech_items.append(tech_item)
        return tech_items

    def infer_tech_type(self, tech: str) -> Optional[str]:
        # Implement logic to determine the type of technology
        frontend_technologies = {'React', 'Vue', 'Angular'}
        backend_technologies = {'Django', 'Flask', 'Node.js'}
        devops_technologies = {'Docker', 'Kubernetes'}
        if tech in frontend_technologies:
            return 'frontend'
        elif tech in backend_technologies:
            return 'backend'
        elif tech in devops_technologies:
            return 'devops'
        else:
            return None

    def infer_tech_level(self, tech: str) -> Optional[str]:
        # Implement logic to determine the level
        primary_technologies = {'Python', 'JavaScript'}
        if tech in primary_technologies:
            return 'primary'
        else:
            return 'secondary'

    def preprocess_domain_expertise(self, domain_list):
        """
        Preprocesses the domain_expertise field to include confidence levels.
        """
        domain_items = []
        if domain_list:
            for domain in domain_list:
                domain_item = {
                    'domain': domain,
                    'confidence_level': self.estimate_confidence_level(domain),
                }
                domain_items.append(domain_item)
        return domain_items

    def estimate_confidence_level(self, domain: str) -> float:
        # Implement logic to estimate confidence level
        # Placeholder implementation
        return 0.8

    def preprocess_growth_timeline(self, row):
        """
        Constructs the growth_timeline field.
        """
        growth_data = []
        founded_on = row.get('founded_on')
        if founded_on is not None and not pd.isnull(founded_on):
            growth_data.append({
                'date': founded_on,
                'company_size': 'startup',
                'funding_total': 0.0,
                'tech_stack': [item['technology'] for item in row.get('tech_stack', [])],
            })
        # Add more data points based on other available data
        return growth_data

    def replace_nan_with_none(self, obj):
        """
        Recursively replaces NaN and NaT values with None in the given data structure.
        """
        if isinstance(obj, dict):
            return {k: self.replace_nan_with_none(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.replace_nan_with_none(v) for v in obj]
        elif isinstance(obj, float) and np.isnan(obj):
            return None
        elif isinstance(obj, (pd.Timestamp, datetime)) and pd.isnull(obj):
            return None
        else:
            return obj

    def infer_missing_data(self, record: dict) -> dict:
        """
        Infers missing data and updates the inferred_attributes list.
        """
        inferred_attrs = record.get('inferred_attributes', [])

        # Example inference for 'company_type'
        if not record.get('company_type') and record.get('operating_status') == 'active':
            record['company_type'] = 'for_profit'  # Default assumption
            inferred_attrs.append('company_type')

        record['inferred_attributes'] = inferred_attrs
        return record

    def calculate_matching_completeness_score(self, record: dict) -> float:
        essential_fields = [
            'company_name',
            'tech_stack',
            'industry',
            'company_size',
            'location',
            'operating_status',
            'company_type',
            'values',
            'company_culture',
        ]
        total_fields = len(essential_fields)
        filled_fields = sum(
            1 for field in essential_fields if record.get(field) not in [None, [], {}, '']
        )
        completeness_score = filled_fields / total_fields if total_fields > 0 else 0
        return round(completeness_score, 2)

    def calculate_general_completeness_score(self, record: dict) -> float:
        total_fields = len(record)
        filled_fields = sum(
            1 for value in record.values() if value not in [None, [], {}, '']
        )
        completeness_score = filled_fields / total_fields if total_fields > 0 else 0
        return round(completeness_score, 2)

    def validate_records(self, records: List[dict]) -> List[CompanyProfile]:
        """
        Validates records using the CompanyProfile Pydantic model.
        """
        validated_records = []
        for record in records:
            try:
                # Replace NaN values with None
                record = self.replace_nan_with_none(record)
                # Infer missing data
                record = self.infer_missing_data(record)
                # Calculate completeness scores
                matching_score = self.calculate_matching_completeness_score(record)
                general_score = self.calculate_general_completeness_score(record)
                record['matching_completeness_score'] = matching_score
                record['general_completeness_score'] = general_score
                # Create a CompanyProfile instance
                company = CompanyProfile(**record)
                # Append the CompanyProfile instance to the list
                validated_records.append(company)
            except ValidationError as e:
                self.logger.warning(f"Validation error for record {record.get('id', 'N/A')}: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error for record {record.get('id', 'N/A')}: {e}")
        return validated_records

    async def insert_records(self, validated_records, start_idx, end_idx):
        """
        Inserts validated records into MongoDB with retry logic.
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Insert records into MongoDB using Beanie
                await CompanyProfile.insert_many(validated_records)
                self.logger.info(f"Successfully inserted {len(validated_records)} records from {start_idx} to {end_idx}")
                break  # Break out of the retry loop if successful
            except Exception as e:
                self.logger.error(f"Batch insert failed for records {start_idx} to {end_idx}: {str(e)}")
                if attempt < max_retries - 1:
                    self.logger.info(f"Retrying batch insert for records {start_idx} to {end_idx} (Attempt {attempt + 2}/{max_retries})")
                    await asyncio.sleep(5)  # Wait before retrying
                else:
                    self.logger.error(f"Batch insert failed after {max_retries} attempts for records {start_idx} to {end_idx}")
                    break  # Break after max retries

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()

    db_uri = os.environ.get('MONGODB_CONNECTION_STRING')
    db_name = os.environ.get('DB_NAME')

    if not db_uri or not db_name:
        logger.error("MongoDB connection string or database name not found in environment variables.")
        raise ValueError("MongoDB connection string or database name not found in environment variables.")

    importer = CompanyImporter(db_uri=db_uri, db_name=db_name)

    # Define the path to the CSV file
    csv_file_path = r"C:\Users\DevX\specialProjects\mAIndScout\crunchbase_companies_data\crunchbase_100k-200k.csv"

    # Remove or comment out this line
    # logging.basicConfig(level=logging.INFO)

    # Start the import process
    asyncio.run(importer.import_companies(csv_file_path, max_entries=100000))

# app/utils/web_scraper_utils.py

import logging
import os
from typing import Optional, Dict
from scrapegraphai.graphs import SearchGraph

class WebScraperUtil:
    def __init__(self):
        """
        Initializes the WebScraperUtil with logging setup.
        """
        # Configure logging to provide detailed output to the console.
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # Define the configuration for the ScrapeGraph pipeline.
        self.graph_config = {
            "llm": {
                "api_key": os.getenv("OPENAI_API_KEY"),  # Use environment variable for security
                "model": "openai/gpt-4o",  # Adjust the model if needed based on pricing/performance
                "rate_limit": {
                    "requests_per_second": 1
        }
            },
            # "library": "selenium",  # Selenium is used for dynamic content handling
            "verbose": True,
            "headless": True,  # Headless browser for efficiency
        }

    def scrape_company_details(self, company_url: str) -> Dict[str, Optional[str]]:
        """
        Scrapes company details using ScrapeGraphAI for more robust extraction.

        Args:
            company_url (str): The URL of the company's website.

        Returns:
            dict: A dictionary containing scraped data (description, industry, tech stack, etc.).
        """
        try:
            # Define the prompt to scrape the required information
            prompt = (
                "Extract company description, industry, location, and technology stack from the website content. if not finding in the main page, search for additional pages in the website"
            )
            self.logger.info(f"Initiating scrape for company URL: {company_url}")
            self.logger.info(f"Prompt being used: {prompt}")

            # Create the SmartScraperGraph instance
            smart_scraper_graph = SearchGraph(
                prompt=prompt,
                # source=company_url,
                config=self.graph_config
            )

            # Run the scraper to get the result
            self.logger.info("Running the scraper...")
            response = smart_scraper_graph.run()
            
            # Extract the data from the response
            self.logger.info("Raw response received: %s", response)

            if "data" in response:
                scraped_data = response["data"]
            else:
                self.logger.warning("No 'data' field in response. Returning empty dictionary.")
                scraped_data = {}

            # Ensure all expected keys are present and fallback to 'N/A' if missing
            company_details = {
                "company_description": scraped_data.get("company_description", "N/A"),
                "industry": scraped_data.get("industry", "N/A"),
                "location": scraped_data.get("location", "N/A"),
                "technology_stack": scraped_data.get("technology_stack", "N/A")
            }

            # Log final extracted data for debugging purposes
            self.logger.info("Extracted company details: %s", company_details)

            return company_details

        except Exception as e:
            self.logger.error(f"Failed to scrape company details from {company_url}: {str(e)}", exc_info=True)
            return {}

# Example usage
if __name__ == "__main__":
    scraper = WebScraperUtil()
    company_data = scraper.scrape_company_details("https://www.slashid.com/")
    print("Scraped Company Data:")
    for key, value in company_data.items():
        print(f"{key}: {value}")

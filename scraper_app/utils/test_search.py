# app/utils/web_scraper_search_utils.py

import logging
import os
import asyncio
import hashlib
import json
from dotenv import load_dotenv
from scrapegraphai.graphs import SearchGraph
from tenacity import retry, stop_after_attempt, wait_random_exponential, retry_if_exception_type
from openai import RateLimitError

class WebScraperSearchUtil:
    def __init__(self):
        """
        Initializes the WebScraperSearchUtil with logging setup, environment variables, and cache for API key.
        """
        self.logger = logging.getLogger(__name__)
        load_dotenv()  # Load environment variables from .env file
        self.api_key = os.getenv("OPENAI_APIKEY")

        # Define the configuration for the SearchGraph
        self.graph_config = {
            "llm": {
                "api_key": self.api_key,
                "model": "openai/gpt-4o",  # Adjust the model if needed based on pricing/performance
                "rate_limit": {
                    "requests_per_second": 1        }
            },
            "max_results": 5,
            "verbose": True,
        }

        # Define cache directory
        self.cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cache')
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def get_cache_key(self, prompt: str) -> str:
        """
        Generates a cache key for a given prompt.
        """
        return hashlib.md5(prompt.encode()).hexdigest()

    def load_from_cache(self, cache_key: str) -> dict:
        """
        Loads the cached response if available.
        """
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.json")
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                self.logger.info(f"Loading cached result for cache key: {cache_key}")
                return json.load(f)
        return {}

    def save_to_cache(self, cache_key: str, data: dict):
        """
        Saves the response data to the cache.
        """
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.json")
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)

    @retry(stop=stop_after_attempt(5), wait=wait_random_exponential(min=1, max=10), retry=retry_if_exception_type(RateLimitError))
    async def run_search_graph(self, prompt: str):
        """
        Executes the SearchGraph with the given prompt and returns the response.

        Args:
            prompt (str): The prompt for the SearchGraph.

        Returns:
            dict: The response from the SearchGraph.
        """
        # Generate cache key for the prompt
        cache_key = self.get_cache_key(prompt)

        # Attempt to load from cache
        cached_response = self.load_from_cache(cache_key)
        if cached_response:
            return cached_response

        # Create the SearchGraph instance
        self.logger.info(f"Running the search graph for prompt: {prompt}")
        search_graph = SearchGraph(
            prompt=prompt,
            config=self.graph_config
        )

        # Run the search graph to get the result asynchronously
        loop = asyncio.get_running_loop()  # Updated to use get_running_loop()
        response = await loop.run_in_executor(None, search_graph.run)
        self.logger.info(f"Raw response received: {response}")

        # Save response to cache
        self.save_to_cache(cache_key, response)

        return response

    async def search_company_details(self, company_name: str):
        """
        Searches for detailed information about the company using ScrapeGraphAI.

        Args:
            company_name (str): The name of the company.

        Returns:
            dict: A dictionary containing the search results.
        """
        try:
            # Define multiple prompts to gather more comprehensive information
            prompts = [
                f"Provide detailed information about the company {company_name}, including its services, industry, and headquarters location.",
                f"Identify {company_name} industry sector and what are the key services and products offered by {company_name}?",
                f"Which technologies, tools, and programming languages are used by employyes at {company_name}?"
            ]

            combined_results = {}

            tasks = [self.run_search_graph(prompt) for prompt in prompts]

            # Run all tasks asynchronously
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            for response in responses:
                if isinstance(response, Exception):
                    self.logger.error(f"Task failed: {response}")
                    continue
                if response:
                    for key, value in response.items():
                        if value and value != "NA":
                            combined_results[key] = value

            # Log the final combined results
            self.logger.info(f"Final Combined Search Data: {combined_results}")

            return combined_results

        except Exception as e:
            self.logger.error(f"Failed to search company details for {company_name}: {str(e)}", exc_info=True)
            return {}

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    scraper = WebScraperSearchUtil()

    # Running asynchronous search
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    company_data = loop.run_until_complete(scraper.search_company_details("Nerdery"))

    print("\nSearch Results for Company:")
    for key, value in company_data.items():
        print(f"{key}: {value}")

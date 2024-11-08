# app/utils/web_scraper_utils.py

import requests
from bs4 import BeautifulSoup
import logging
import re
from typing import Optional, Dict, List

class WebScraperUtil:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

    def scrape_company_details(self, company_url: str) -> Dict[str, Optional[str]]:
        """
        Scrapes company details such as description, industry, tech stack, and more from the given URL.

        Args:
            company_url (str): The URL of the company's website.

        Returns:
            dict: A dictionary containing scraped data (description, industry, tech stack, etc.).
        """
        try:
            response = requests.get(company_url, headers=self.headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch the URL {company_url}: {str(e)}", exc_info=True)
            return {}

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        scraped_data = {
            "description": self.extract_meta_description(soup),
            "industry": self.extract_industry(soup),
            "about": self.extract_about_section(soup),
            "tech_stack": self.extract_tech_stack(soup),
            "location": self.extract_location(soup)
        }

        return scraped_data

    def extract_meta_description(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extracts the meta description from the HTML soup.

        Args:
            soup (BeautifulSoup): Parsed HTML content.

        Returns:
            str or None: The meta description if found.
        """
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and "content" in meta.attrs:
            return meta.attrs["content"].strip()
        return None

    def extract_industry(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Attempts to extract the industry information from the company's website.
        This method uses keywords and scans the page for common industry terms.

        Args:
            soup (BeautifulSoup): Parsed HTML content.

        Returns:
            str or None: The identified industry if found.
        """
        keywords = ["industry", "sector", "field"]
        paragraphs = soup.find_all("p")
        for paragraph in paragraphs:
            text = paragraph.get_text().lower()
            if any(keyword in text for keyword in keywords):
                return paragraph.get_text().strip()
        return None

    def extract_about_section(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extracts text from sections of the website that are typically labeled as "About Us".

        Args:
            soup (BeautifulSoup): Parsed HTML content.

        Returns:
            str or None: The "About Us" section content if found.
        """
        about_section = soup.find(lambda tag: tag.name in ["div", "section"] and "about" in tag.get_text().lower())
        if about_section:
            return about_section.get_text().strip()
        return None

    def extract_tech_stack(self, soup: BeautifulSoup) -> Optional[List[str]]:
        """
        Attempts to extract the technologies or tech stack used by the company from the website content.

        Args:
            soup (BeautifulSoup): Parsed HTML content.

        Returns:
            list or None: A list of technologies mentioned on the website.
        """
        keywords = ["JavaScript", "Python", "React", "Angular", "Django", "Flask", "Node.js", "AWS", "Azure"]
        tech_stack = []
        for script_tag in soup.find_all("script"):
            script_content = script_tag.get_text().lower()
            for keyword in keywords:
                if keyword.lower() in script_content and keyword not in tech_stack:
                    tech_stack.append(keyword)
        for paragraph in soup.find_all("p"):
            paragraph_content = paragraph.get_text().lower()
            for keyword in keywords:
                if keyword.lower() in paragraph_content and keyword not in tech_stack:
                    tech_stack.append(keyword)
        return tech_stack if tech_stack else None

    def extract_location(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Attempts to extract the location information from the company's website.

        Args:
            soup (BeautifulSoup): Parsed HTML content.

        Returns:
            str or None: The identified location if found.
        """
        address_keywords = ["address", "location", "headquarters"]
        paragraphs = soup.find_all("p")
        for paragraph in paragraphs:
            text = paragraph.get_text().lower()
            if any(keyword in text for keyword in address_keywords):
                return paragraph.get_text().strip()
        return None

# Example usage
if __name__ == "__main__":
    scraper = WebScraperUtil()
    company_data = scraper.scrape_company_details("https://example.com")
    print(company_data)

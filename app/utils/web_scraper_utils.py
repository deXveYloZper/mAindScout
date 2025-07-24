# app/utils/web_scraper_utils.py
import logging
import httpx
from typing import Dict, Optional, List
from bs4 import BeautifulSoup
import re
import asyncio

class WebScraperUtil:
    def __init__(self, timeout: int = 10, delay: float = 1.0):
        self.logger = logging.getLogger(__name__)
        self.timeout = timeout
        self.delay = delay
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    async def scrape_company_details(self, url: str) -> Dict:
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                self.logger.info(f"Scraping company details from: {url}")
                response = await client.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'lxml') # Using lxml parser
                company_data = {
                    'description': self._extract_description(soup),
                    'industry': self._extract_industry(soup),
                    'location': self._extract_location(soup),
                    'tech_stack': self._extract_tech_stack(soup),
                    'company_size': self._extract_company_size(soup),
                    'founded_year': self._extract_founded_year(soup)
                }
                return {k: v for k, v in company_data.items() if v is not None}
        except httpx.RequestError as e:
            self.logger.error(f"Request error scraping {url}: {str(e)}")
            return {}
        finally:
            await asyncio.sleep(self.delay)

    # --- Helper methods copied from the original file ---
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()
        desc_selectors = [
            '.description', '.about', '.company-description', 
            '.about-us', '.company-about', '[class*="description"]'
        ]
        for selector in desc_selectors:
            element = soup.select_one(selector)
            if element and element.get_text().strip():
                return element.get_text().strip()[:500]
        return None

    def _extract_industry(self, soup: BeautifulSoup) -> Optional[str]:
        industry_keywords = ['industry', 'sector', 'business', 'technology', 'software', 'healthcare', 'finance']
        for keyword in industry_keywords:
            meta = soup.find('meta', attrs={'name': keyword})
            if meta and meta.get('content'):
                return meta['content'].strip()
        text = soup.get_text().lower()
        for keyword in industry_keywords:
            if keyword in text:
                sentences = re.split(r'[.!?]', text)
                for sentence in sentences:
                    if keyword in sentence:
                        return sentence.strip()[:100]
        return None

    def _extract_location(self, soup: BeautifulSoup) -> Optional[str]:
        location_selectors = [
            '.address', '.location', '.contact', '.office',
            '[class*="address"]', '[class*="location"]'
        ]
        for selector in location_selectors:
            element = soup.select_one(selector)
            if element and element.get_text().strip():
                return element.get_text().strip()
        location_meta = soup.find('meta', attrs={'name': 'geo.region'})
        if location_meta and location_meta.get('content'):
            return location_meta['content'].strip()
        return None

    def _extract_tech_stack(self, soup: BeautifulSoup) -> List[str]:
        tech_stack = []
        tech_keywords = [
            'python', 'javascript', 'react', 'angular', 'vue', 'node.js', 'java', 'c#', 'php',
            'aws', 'azure', 'google cloud', 'docker', 'kubernetes', 'mongodb', 'postgresql',
            'mysql', 'redis', 'elasticsearch', 'kafka', 'spark', 'tensorflow', 'pytorch'
        ]
        text = soup.get_text().lower()
        for tech in tech_keywords:
            if tech in text:
                tech_stack.append(tech.title())
        return tech_stack

    def _extract_company_size(self, soup: BeautifulSoup) -> Optional[str]:
        size_keywords = ['employees', 'team size', 'company size', 'staff']
        text = soup.get_text().lower()
        for keyword in size_keywords:
            if keyword in text:
                sentences = re.split(r'[.!?]', text)
                for sentence in sentences:
                    if keyword in sentence:
                        return sentence.strip()[:100]
        return None

    def _extract_founded_year(self, soup: BeautifulSoup) -> Optional[int]:
        text = soup.get_text()
        year_pattern = r'\b(19[0-9]{2}|20[0-2][0-4])\b'
        years = re.findall(year_pattern, text)
        if years:
            return min(int(year) for year in years)
        return None 
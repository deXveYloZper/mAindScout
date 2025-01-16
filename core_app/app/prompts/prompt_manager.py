# app/prompts/prompt_manager.py

from app.prompts.job_prompts import TECH_JOB_DESCRIPTION_EXTRACTION_PROMPT
from app.prompts.candidate_prompts import TECH_CANDIDATE_PROFILE_EXTRACTION_PROMPT

class PromptManager:
    @staticmethod
    def get_job_prompt(domain: str) -> str:
        if domain == "tech":
            return TECH_JOB_DESCRIPTION_EXTRACTION_PROMPT
        # Add more domains as needed
        else:
            raise ValueError(f"No prompt found for domain: {domain}")

    @staticmethod
    def get_candidate_prompt(domain: str) -> str:
        if domain == "tech":
            return TECH_CANDIDATE_PROFILE_EXTRACTION_PROMPT
        # Add more domains as needed
        else:
            raise ValueError(f"No prompt found for domain: {domain}")

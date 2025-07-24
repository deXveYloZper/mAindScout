# app/utils/openai_utils.py
import openai
import json
import logging
from app.core.config import settings
logger = logging.getLogger(__name__)
# Initialize the new OpenAI client
client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
def extract_info_from_text(text: str, prompt: str) -> dict:
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        response_content = response.choices[0].message.content
        return json.loads(response_content)
    except openai.RateLimitError as e:
        logger.error(f"OpenAI Rate Limit Error: {e}")
        raise ValueError("OpenAI API rate limit exceeded.") from e
    except openai.APIError as e:
        logger.error(f"OpenAI API Error: {e}")
        raise ValueError("An error occurred with the OpenAI API.") from e
    except Exception as e:
        logger.error(f"An unexpected error occurred during OpenAI extraction: {e}")
        raise
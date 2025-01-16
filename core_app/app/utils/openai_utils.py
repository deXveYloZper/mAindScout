# app/utils/openai_utils.py

import openai
from openai import OpenAIError, APIError, RateLimitError, APIConnectionError

from app.core.config import settings
import json5
import logging
import time

logger = logging.getLogger(__name__)

# Initialize the OpenAI API client with the provided API key
openai.api_key = settings.OPENAI_API_KEY

def extract_info_from_text(text: str, prompt: str) -> dict:
    """
    Function to extract structured information from text using OpenAI's GPT model.

    Args:
    - prompt (str): The complete prompt to guide the model.

    Returns:
    - dict: A dictionary with extracted information.
    """
    max_retries = 3
    retry_delay = 2  # in seconds
    token_threshold = 8192  # Threshold for using GPT-4-32k

     # Estimate the number of tokens needed (approximately, for safety)
    estimated_tokens = len(text.split()) + len(prompt.split())

    # Choose the appropriate model based on estimated token length
    if estimated_tokens > token_threshold:
        model_to_use = "gpt-4-32k-0314"
        logger.info("Switching to GPT-4-32k model due to large token size.")
    else:
        model_to_use = "gpt-4o"
        logger.info("Using GPT-4 (8k tokens) model for this request.")


    for attempt in range(max_retries):
        try:    
            # Send a request to OpenAI API with the text and prompt
            
            response = openai.chat.completions.create(
                model=model_to_use,
                messages=[
                    {"role": "system", "content": " You will be provided with unstructured CV, parsed by pdfplumber. Your task is to extract data according to the prompt. Please follow the user prompt:"},
                    {"role": "user", "content": f"{prompt}\n{text}"}
                ],
                max_tokens=5000,
                temperature=0.2  # Adjust as needed
            )
            
            # Parse the response to extract the relevant data
            structured_data = response.choices[0].message.content.strip()

            # Log the raw JSON output for debugging
            logger.debug(f"Raw OpenAI Output:\n{structured_data}")  
            
            # Handle the response possibly wrapped in code block markers
            if structured_data.startswith("```json"):
                structured_data = structured_data.strip("```json").strip().strip("```")

            # Attempt to parse as JSON5
            try:
                extracted_data = json5.loads(structured_data)
            except json5.JSONDecodeError as json_error:
                logger.error(f"JSON5 decoding error: {str(json_error)}")
                raise ValueError(f"Failed to parse OpenAI response as JSON5: {str(json_error)}") from json_error

            return extracted_data
        
        except (APIError, RateLimitError,
                APIConnectionError) as e:  # Catch specific OpenAI errors
            logger.error(
                f"OpenAI API error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                continue
            else:
                raise ValueError(
                    f"Failed to extract information using OpenAI after {max_retries} attempts: {str(e)}"
                ) from e
        except json5.JSONDecodeError as e:
            logger.error(f"JSON decoding error: {str(e)}")
            raise ValueError(
                f"Failed to parse OpenAI response as JSON: {str(e)}") from e

        except Exception as e:
            logger.error(
                f"OpenAI Error: {str(e)}, Prompt: {prompt}, Text Length: {len(text)}"
            )
            raise ValueError(
                f"Failed to extract information using OpenAI: {str(e)}")
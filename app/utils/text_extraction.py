# app/utils/text_extraction.py

import pdfplumber
import docx
from fastapi import UploadFile
from typing import Union
import logging
import io
import re

logger = logging.getLogger(__name__)

async def extract_text_from_file(file: UploadFile) -> str:
    """
    Extract text from an uploaded file based on its format.

    Supported formats:
    - PDF
    - DOCX
    - Plain text

    Args:
    - file (UploadFile): The uploaded file.

    Returns:
    - str: Sanitized text extracted from the file.

    Raises:
    - ValueError: If the file format is unsupported or text extraction fails.
    """
    try:
        # Read the file content
        content = await file.read()
        file_extension = file.filename.split('.')[-1].lower()

        # Reset the file pointer
        file.file.seek(0)

        if file.content_type == "application/pdf" or file_extension == "pdf":
            extracted_text = extract_text_from_pdf(file)
        elif file.content_type in [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword"
        ] or file_extension in ["docx", "doc"]:
            extracted_text = extract_text_from_docx(file)
        elif file.content_type == "text/plain" or file_extension == "txt":
            extracted_text = await extract_text_from_plain_text(file)
        else:
            raise ValueError("Unsupported file format. Please upload a PDF, DOCX, or plain text file.")

        # Sanitize the extracted text
        sanitized_text = sanitize_text(extracted_text)
        return sanitized_text

    except Exception as e:
        logger.error(f"Error extracting text from file: {str(e)}")
        raise ValueError(f"Failed to extract text: {str(e)}") from e

def extract_text_from_pdf(file: UploadFile) -> str:
    """
    Extract text from a PDF file.

    Args:
    - file (UploadFile): The uploaded PDF file.

    Returns:
    - str: Extracted text from the PDF.
    """
    try:
        with pdfplumber.open(file.file) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {str(e)}")
        raise ValueError(f"Failed to extract text from PDF file: {str(e)}") from e

def extract_text_from_docx(file: UploadFile) -> str:
    """
    Extract text from a DOCX or DOC file.

    Args:
    - file (UploadFile): The uploaded DOCX or DOC file.

    Returns:
    - str: Extracted text from the DOCX/DOC.
    """
    try:
        # For DOC files, use alternative libraries if necessary
        if file.filename.lower().endswith('.doc'):
            # Placeholder: Implement .doc file extraction if needed
            raise ValueError("DOC format is not supported at this time.")
        else:
            doc = docx.Document(file.file)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text.strip()
    except Exception as e:
        logger.error(f"Failed to extract text from DOCX/DOC: {str(e)}")
        raise ValueError(f"Failed to extract text from DOCX/DOC file: {str(e)}") from e

async def extract_text_from_plain_text(file: UploadFile) -> str:
    """
    Extract text from a plain text file.

    Args:
    - file (UploadFile): The uploaded plain text file.

    Returns:
    - str: Extracted text from the plain text file.
    """
    try:
        text = await file.read()
        return text.decode("utf-8").strip()
    except Exception as e:
        logger.error(f"Failed to extract text from plain text file: {str(e)}")
        raise ValueError(f"Failed to extract text from plain text file: {str(e)}") from e

def sanitize_text(text: str) -> str:
    """
    Sanitize extracted text to remove malicious content or scripts.

    Args:
    - text (str): The text to sanitize.

    Returns:
    - str: Sanitized text.
    """
    try:
        # Remove any HTML tags or scripts
        clean_text = re.sub(r'<[^>]+>', '', text)

        # Remove any JavaScript or embedded scripts
        clean_text = re.sub(r'<script.*?>.*?</script>', '', clean_text, flags=re.DOTALL | re.IGNORECASE)

        # Additional sanitization rules can be added here

        return clean_text.strip()
    except Exception as e:
        logger.error(f"Error sanitizing text: {str(e)}")
        raise ValueError(f"Failed to sanitize text: {str(e)}") from e

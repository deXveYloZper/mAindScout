# app/api/endpoints.py

from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form, BackgroundTasks, Request
from pydantic import ValidationError
from app.schemas.job_schema import JobDescription
from app.schemas.candidate_schema import CandidateProfile, CandidateMatch
from app.services.job_service import JobService
from app.services.candidate_service import CandidateService
from app.core.logging import logger
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import List
from app.utils.text_extraction import extract_text_from_file
from app.utils.openai_utils import extract_info_from_text
from enum import Enum

limiter = Limiter(key_func=get_remote_address)

file_upload_router = APIRouter()
job_router = APIRouter()
candidate_router = APIRouter()

# Define an Enum for file types to enforce allowed values
class FileType(str, Enum):
    JOB_DESCRIPTION = "job_description"
    CANDIDATE_PROFILE = "candidate_profile"

@file_upload_router.post("/upload", response_model=dict)
async def upload_file(
    file: UploadFile = File(...),
    file_type: FileType = Form(...)
):
    """
    Endpoint to upload a file, either a job description or a candidate profile.

    - Validates the file type and content type.
    - Extracts text from the file using `extract_text_from_file`.
    - Processes the extracted text accordingly.
    """
    # Allowed content types for file uploads
    allowed_content_types = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    ]

    try:
        # Validate file content type
        if file.content_type not in allowed_content_types:
            logger.warning(f"Unsupported file type: {file.content_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.content_type}. Please upload a PDF, DOCX, or plain text file."
            )

        # Limit file size to prevent large uploads (e.g., 5MB)
        MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            logger.warning(f"File too large: {file.filename} ({len(content)} bytes)")
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds the maximum allowed size of 5 MB."
            )
        # Reset file pointer after reading
        file.file.seek(0)

        # Extract text from the uploaded file
        extracted_text = await extract_text_from_file(file)
        if not extracted_text:
            raise ValueError("Failed to extract text from the file.")

        if file_type == FileType.JOB_DESCRIPTION:
            job_service = JobService()
            # Process the extracted text to create a job description
            job_data = job_service.create_job_description(extracted_text)
            logger.info(f"Job description processed: {job_data.title}")
            return {"message": "Job description processed successfully", "job_data": job_data.model_dump()}

        elif file_type == FileType.CANDIDATE_PROFILE:
            candidate_service = CandidateService()
            # Process the extracted text to create a candidate profile
            candidate_profile = candidate_service.parse_and_store_candidate_profile(extracted_text)
            logger.info(f"Candidate profile processed: {candidate_profile.name}")
            return {"message": "CV processed successfully", "candidate_profile": candidate_profile.model_dump()}

        else:
            logger.error(f"Invalid file_type parameter: {file_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file_type parameter"
            )

    except HTTPException as e:
        # Re-raise HTTP exceptions to be handled by FastAPI
        logger.error(f"HTTPException in upload_file: {e.detail}, File Name: {file.filename}, Content Type: {file.content_type}")
        raise e
    except ValidationError as e:
        logger.error(f"ValidationError in upload_file: {str(e)}, File Name: {file.filename}, Content Type: {file.content_type}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in upload_file: {str(e)}, File Name: {file.filename}, Content Type: {file.content_type}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the file."
        )   

@job_router.post("/", response_model=dict)
@limiter.limit("5/minute")
async def create_job_description(request: Request, job_description: JobDescription):
    """
    API endpoint to create a new job description.

    - Accepts a job description as input.
    - Validates and saves the job description using the JobService.
    - Returns a success message if the operation is successful.
    - Rate-limited to 5 requests per minute per IP address.
    """
    try:
        job_service = JobService()
        await job_service.create_job_description(job_description)
        logger.info(f"Job description created: {job_description.title}")
        return {"message": "Job description created successfully"}
    except ValidationError as e:
        logger.error(f"Validation error in create_job_description: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error in create_job_description: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@candidate_router.post("/match", response_model=dict)
@limiter.limit("2/minute")
async def match_candidates(request: Request, job_description: JobDescription, background_tasks: BackgroundTasks):
    """
    API endpoint to start the candidate matching process for a given job description.

    - Accepts a job description as input.
    - Starts the matching process in the background.
    - Returns a message indicating that the matching process has started.
    - Rate-limited to 2 requests per minute per IP address.
    """
    try:
        candidate_service = CandidateService()
        background_tasks.add_task(candidate_service.match_candidates, job_description)
        logger.info(f"Started matching candidates for job: {job_description.title}")
        return {"message": "Candidate matching process started"}
    except ValidationError as e:
        logger.error(f"Validation error in match_candidates: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error in match_candidates: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@candidate_router.get("/match/{job_id}", response_model=List[CandidateMatch])
@limiter.limit("10/minute")
async def get_matched_candidates(request: Request, job_id: str):
    """
    API endpoint to retrieve matched candidates for a given job.

    - Accepts a job ID as a path parameter.
    - Retrieves the list of matched candidates from the CandidateService.
    - Returns the list of matched candidates.
    - Rate-limited to 10 requests per minute per IP address.
    """
    try:
        candidate_service = CandidateService()
        matches = await candidate_service.get_matched_candidates(job_id)
        if not matches:
            logger.info(f"No matches found for job_id: {job_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No matching candidates found")
        logger.info(f"Retrieved {len(matches)} matches for job_id: {job_id}")
        return matches
    except Exception as e:
        logger.error(f"Error in get_matched_candidates: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

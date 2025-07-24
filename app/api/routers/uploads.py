# app/api/routers/uploads.py
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form, Request, Depends
from app.core.logging import logger
from app.core.limiter import limiter
from app.api.dependencies import get_job_service, get_candidate_service
from app.services.job_service import JobService
from app.services.candidate_service import CandidateService
from enum import Enum

file_upload_router = APIRouter()

class FileType(str, Enum):
    JOB_DESCRIPTION = "job_description"
    CANDIDATE_PROFILE = "candidate_profile"

@file_upload_router.post("/upload", response_model=dict)
@limiter.limit("20/minute")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    file_type: FileType = Form(...),
    candidate_service: CandidateService = Depends(get_candidate_service),
    job_service: JobService = Depends(get_job_service)
):
    allowed_content_types = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    ]
    if file.content_type not in allowed_content_types:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")
    try:
        if file_type == FileType.CANDIDATE_PROFILE:
            candidate_profile = await candidate_service.parse_and_store_candidate_profile_from_file(file)
            logger.info(f"Candidate profile processed: {candidate_profile.name}")
            return {"message": "CV processed successfully", "candidate_profile": candidate_profile.model_dump(mode='json')}
        elif file_type == FileType.JOB_DESCRIPTION:
            job_data = await job_service.parse_and_store_job_description_from_file(file)
            logger.info(f"Job description processed: {job_data.title}")
            return {"message": "Job description processed successfully", "job_data": job_data.model_dump(mode='json')}
    except Exception as e:
        logger.error(f"Error in upload_file: {str(e)}, File Name: {file.filename}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while processing the file.") 
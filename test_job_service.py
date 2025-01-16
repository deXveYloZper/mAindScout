# test_job_service.py

import asyncio
from fastapi import UploadFile
from core_app.app.services.job_service import JobService
from core_app.app.core.config import settings

async def test_job_service():
    # Step 1: Set up the JobService instance
    job_service = JobService(db_uri=settings.MONGODB_CONNECTION_STRING, db_name=settings.DB_NAME)

    # Step 2: Provide the test file path (PDF)
    file_path = "golang_job_advert.pdf"  # Make sure this file exists in the same directory

    # Step 3: Open the file as an UploadFile
    with open(file_path, "rb") as file:
        upload_file = UploadFile(filename=file_path, file=file)

        # Step 4: Process the job description from the file
        try:
            job_description = await job_service.create_job_description_from_file(upload_file)
            print(f"Successfully created job with ID: {job_description.id}")
        except ValueError as e:
            print(f"Error during job creation: {e}")

# Running the test with asyncio
if __name__ == "__main__":
    asyncio.run(test_job_service())

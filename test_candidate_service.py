# test_candidate_service.py

import asyncio
import pdfplumber
from fastapi import UploadFile
from core_app.app.services.candidate_service import CandidateService
from core_app.app.core.config import settings

async def test_candidate_service():
    # Step 1: Set up the CandidateService instance
    candidate_service = CandidateService(db_uri=settings.MONGODB_CONNECTION_STRING, db_name=settings.DB_NAME)

    # Step 2: Provide the test file path (PDF or Text File)
    file_path = "foti_Dimanidis_Resume.pdf"  # Make sure this file exists in the same directory

   # Step 3: Open the file and extract text
    try:
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"

        # Step 4: Process the candidate profile from the extracted text
        try:
            # Since `parse_and_store_candidate_profile` is not an async function, remove `await`
            candidate_profile = candidate_service.parse_and_store_candidate_profile(text)
            
            # Access the correct attribute for the candidate profile id
            if hasattr(candidate_profile, 'id'):
                print(f"Successfully created candidate profile with ID: {candidate_profile.id}")
            else:
                print("Successfully created candidate profile, but ID could not be found.")

        except ValueError as e:
            print(f"Error during candidate profile creation: {e}")

    except Exception as e:
        print(f"Error reading the PDF file: {e}")

# Running the test with asyncio
if __name__ == "__main__":
    asyncio.run(test_candidate_service())
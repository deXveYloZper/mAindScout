# # app/services/candidate_service.py
# from pymongo import MongoClient
# from app.core.config import Settings
# from app.core.models import JobDescription, CandidateProfile
# from app.utils.data_processing import extract_job_features, score_candidate
# from pinecone import Index
# import re
# from typing import List

# class CandidateService:
#     def __init__(self):
#         # Initialize a connection to the MongoDB client using the connection string from settings
#         self.client = MongoClient(Settings.MONGODB_CONNECTION_STRING)
        
#         # Access the specific database within MongoDB
#         self.db = self.client[Settings.MONGODB_DATABASE_NAME]
        
#         # Reference the collection that stores candidate profiles
#         self.candidate_profiles = self.db["candidate_profiles"]
        
#         # Initialize the Pinecone index for vector similarity search using the index name from settings
#         self.index = Index(Settings.PINECONE_INDEX_NAME)

#     def match_candidates(self, job_description: JobDescription):
#         """
#         Match candidates against a job description using vector similarity.

#         Args:
#         - job_description (JobDescription): The job description object to match candidates against.

#         Returns:
#         - List[CandidateProfile]: The top 5 candidate profiles that best match the job description.
#         """
#         # Extract key features from the job description to generate a feature vector
#         job_features = extract_job_features(job_description)

#         # Perform a vector search in the Pinecone index to find the top 10 candidate profiles
#         # that are most similar to the job description's features
#         candidate_ids = self.index.search(job_features, top_k=10)

#         # Initialize an empty list to store the candidates and their match scores
#         candidates = []

#         # Iterate over the candidate IDs returned by the Pinecone search
#         for candidate_id in candidate_ids:
#             # Retrieve the candidate profile from MongoDB using the candidate ID
#             candidate = self.candidate_profiles.find_one({"_id": candidate_id})
            
#             # Convert the MongoDB document into a CandidateProfile object
#             candidate_profile = CandidateProfile(**candidate)
            
#             # Calculate the match score between the candidate profile and the job features
#             score = score_candidate(candidate_profile, job_features)
            
#             # Append the candidate and their score to the list
#             candidates.append({"candidate": candidate_profile, "score": score})

#         # Sort the candidates by their score in descending order
#         candidates.sort(key=lambda x: x["score"], reverse=True)
        
#         # Return the top 5 candidates based on their match score
#         return [c["candidate"] for c in candidates[:5]]

#     def parse_and_store_candidate_profile(self, text: str) -> CandidateProfile:
#         """
#         Parse a candidate's profile from extracted CV text and store it in MongoDB.

#         Args:
#         - text (str): Extracted text from a candidate's CV.

#         Returns:
#         - CandidateProfile: The parsed candidate profile.
#         """
#         # Parse the extracted text to create a CandidateProfile object
#         candidate_profile = self.parse_candidate_profile(text)
        
#         # Convert the CandidateProfile to a dictionary and store it in MongoDB
#         self.candidate_profiles.insert_one(candidate_profile.model_dump())

#         # Return the created CandidateProfile object
#         return candidate_profile

#     def parse_candidate_profile(self, text: str) -> CandidateProfile:
#         """
#         Parse the extracted text from a CV into a structured CandidateProfile object.

#         Args:
#         - text (str): Extracted text from the candidate's CV.

#         Returns:
#         - CandidateProfile: Structured candidate profile data.
#         """
#         # Extract different pieces of information from the CV text
#         name = self.extract_name(text)
#         email = self.extract_email(text)
#         skills = self.extract_skills(text)
#         experience_years = self.extract_experience_years(text)
#         current_role = self.extract_current_role(text)
#         location = self.extract_location(text)
        
#         # Placeholder for generating vector embeddings using NLP models
#         vector_embedding = self.generate_vector_embedding(skills)
        
#         # Create and return a CandidateProfile object
#         return CandidateProfile(
#             name=name,
#             email=email,
#             skills=skills,
#             experience_years=experience_years,
#             current_role=current_role,
#             location=location,
#             vector_embedding=vector_embedding
#         )

#     def extract_name(self, text: str) -> str:
#         """
#         Extract the candidate's name from the CV text.

#         Args:
#         - text (str): Extracted CV text.

#         Returns:
#         - str: The candidate's name or 'Unknown' if not found.
#         """
#         match = re.search(r'(?:Name|Full Name|Candidate Name):\s*([\w\s]+)', text, re.IGNORECASE)
#         return match.group(1).strip() if match else "Unknown"

#     def extract_email(self, text: str) -> str:
#         """
#         Extract the candidate's email from the CV text.

#         Args:
#         - text (str): Extracted CV text.

#         Returns:
#         - str: The candidate's email or 'Unknown' if not found.
#         """
#         match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
#         return match.group(0).strip() if match else "Unknown"

#     def extract_skills(self, text: str) -> List[str]:
#         """
#         Extract the candidate's skills from the CV text.

#         Args:
#         - text (str): Extracted CV text.

#         Returns:
#         - List[str]: A list of skills (placeholder values used for now).
#         """
#         # A placeholder for skill extraction logic
#         # This can be expanded with NLP-based extraction or keyword matching
#         return ["Python", "Django", "Machine Learning"]

#     def extract_experience_years(self, text: str) -> int:
#         """
#         Extract the candidate's years of experience from the CV text.

#         Args:
#         - text (str): Extracted CV text.

#         Returns:
#         - int: The number of years of experience.
#         """
#         match = re.search(r'(\d+)\s+years\s+of\s+experience', text, re.IGNORECASE)
#         return int(match.group(1)) if match else 0

#     def extract_current_role(self, text: str) -> str:
#         """
#         Extract the candidate's current role from the CV text.

#         Args:
#         - text (str): Extracted CV text.

#         Returns:
#         - str: The candidate's current role or 'Unknown' if not found.
#         """
#         match = re.search(r'(?:Role|Position|Title):\s*([\w\s]+)', text, re.IGNORECASE)
#         return match.group(1).strip() if match else "Unknown"

#     def extract_location(self, text: str) -> str:
#         """
#         Extract the candidate's location from the CV text.

#         Args:
#         - text (str): Extracted CV text.

#         Returns:
#         - str: The candidate's location or 'Unknown' if not found.
#         """
#         match = re.search(r'(?:Location|City|Place):\s*([\w\s,]+)', text, re.IGNORECASE)
#         return match.group(1).strip() if match else "Unknown"

#     def generate_vector_embedding(self, skills: List[str]) -> List[float]:
#         """
#         Generate a vector embedding for the candidate's skills.

#         Args:
#         - skills (List[str]): A list of the candidate's skills.

#         Returns:
#         - List[float]: A placeholder vector representation of the skills.
#         """
#         # Placeholder for generating vector embeddings using NLP models
#         return [0.1, 0.2, 0.3]  # Example vector

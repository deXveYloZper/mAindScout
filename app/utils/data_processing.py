# app/utils/data_processing.py

from typing import List
from app.core.models import JobDescription, CandidateProfile

# Assuming that the necessary NLP models and geospatial models are pre-loaded
# We'll add imports and initialization for the models used in encoding
from sentence_transformers import SentenceTransformer  # Example for NLP model
from geopy.geocoders import Nominatim  # Example for geospatial encoding

# Initialize the models
skill_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')  # Example pre-trained NLP model
geolocator = Nominatim(user_agent="geoapiExercises")  # Example geospatial model

def extract_job_features(job_description: JobDescription) -> List[float]:
    """
    This function takes a job description and extracts the key features
    that will be used for candidate matching. It creates a vector
    representation of the job requirements.
    """
    # Extract feature vectors from the job description components
    skills_vector = encode_skills(job_description.required_skills)
    experience_vector = encode_experience_level(job_description.experience_level)
    location_vector = encode_location(job_description.location)

    # Combine the feature vectors into a single representation
    job_features = skills_vector + experience_vector + location_vector
    return job_features

def score_candidate(candidate: CandidateProfile, job_features: List[float], job_description: JobDescription) -> float:
    """
    This function takes a candidate profile, the job features, and the job description,
    and calculates a score representing how well the candidate matches the job.
    
    Args:
    - candidate (CandidateProfile): The profile of the candidate being evaluated.
    - job_features (List[float]): A list of feature vectors extracted from the job description.
    - job_description (JobDescription): The job description against which the candidate is being evaluated.

    Returns:
    - float: A score representing how well the candidate matches the job, where higher is better.
    """
    # Calculate the cosine similarity between the candidate's vector embedding
    # and the job features vector. This measures the similarity between the candidate's profile
    # and the job requirements.
    similarity = cosine_similarity(candidate.vector_embedding, job_features)

    # Calculate the experience ratio, which is the candidate's years of experience
    # divided by the expected years of experience for the job (converted from the job's experience level).
    # This ensures that candidates with appropriate experience levels are scored higher.
    experience_ratio = candidate.experience_years / experience_level_to_years(job_description.experience_level)
    
    # Calculate the final score by multiplying the similarity by the experience ratio.
    # This combines the similarity of the candidate's skills with how well their experience level matches.
    score = similarity * experience_ratio
    
    return score


def encode_skills(skills: List[str]) -> List[float]:
    """
    This function takes a list of skills and encodes them into a vector
    representation using a pre-trained NLP model.
    """
    # Use the NLP model to encode each skill into a vector and aggregate them
    skills_vector = []
    for skill in skills:
        skill_vector = skill_model.encode(skill)
        skills_vector.extend(skill_vector)
    return skills_vector

def encode_experience_level(experience_level: str) -> List[float]:
    """
    This function takes an experience level and encodes it into a vector
    representation.
    """
    # Use a simple encoding scheme to represent the experience level
    experience_mapping = {
        "entry-level": [1, 0, 0],
        "mid-level": [0, 1, 0],
        "senior-level": [0, 0, 1]
    }
    return experience_mapping[experience_level]

def encode_location(location: str) -> List[float]:
    """
    This function takes a location and encodes it into a vector
    representation using a pre-trained geospatial model.
    """
    # Encode the location using the geospatial model
    location_obj = geolocator.geocode(location)
    location_vector = [location_obj.latitude, location_obj.longitude]
    return location_vector

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    This function calculates the cosine similarity between two vectors.
    """
    dot_product = sum(x * y for x, y in zip(vec1, vec2))
    norm1 = sum(x ** 2 for x in vec1) ** 0.5
    norm2 = sum(y ** 2 for y in vec2) ** 0.5
    return dot_product / (norm1 * norm2)

def experience_level_to_years(experience_level: str) -> int:
    """
    This helper function converts experience levels to approximate years of experience.
    """
    mapping = {
        "entry-level": 1,
        "mid-level": 5,
        "senior-level": 10
    }
    return mapping.get(experience_level, 1)  # Default to 1 year if undefined

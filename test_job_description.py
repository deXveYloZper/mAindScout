from app.core.models import JobDescription
from app.utils.data_processing import extract_job_features

# Example job description as a string
job_description_text = """
Senior Python Developer

We are looking for an experienced Python Developer with a deep understanding of Django, RESTful APIs, and database management. The ideal candidate will have experience in designing and implementing complex web applications, working in an Agile environment, and leading a team of junior developers.

Required Skills:
- Python
- Django
- REST APIs
- Database Management

Experience Level:
- Senior-level

Location:
- Remote
"""

# Simulate a job description object (manually created for testing purposes)
job_description = JobDescription(
    title="Senior Python Developer",
    description=job_description_text,
    required_skills=["Python", "Django", "REST APIs", "Database Management"],
    experience_level="senior-level",
    location="Remote"
)

# Call the feature extraction function
job_features = extract_job_features(job_description)

# Print the extracted features
print("Extracted Job Features:")
print(job_features)

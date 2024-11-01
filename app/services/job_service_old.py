# from app.core.config import Settings
# from app.core.models import JobDescription
# from pymongo import MongoClient

# class JobService:
#     def __init__(self):
#         # Initialize a connection to the MongoDB client using the connection string from settings
#         self.client = MongoClient(Settings.MONGODB_CONNECTION_STRING)
        
#         # Access the specific database within MongoDB
#         self.db = self.client[Settings.MONGODB_DATABASE_NAME]
        
#         # Reference the collection that stores job descriptions
#         self.job_descriptions = self.db["job_descriptions"]

#     def create_job_description(self, job_description: JobDescription):
#         # Insert the job description into the MongoDB collection
#         # The job description is converted to a dictionary using model_dump(), which is the Pydantic v2 replacement for dict()
#         self.job_descriptions.insert_one(job_description.model_dump())

from pymongo import MongoClient
from app.core.config import settings

class MongoDB:
    def __init__(self):
        self.client = MongoClient(settings.MONGODB_URL)
        self.db = self.client[settings.DB_NAME]

db_manager = MongoDB()

def get_database():
    return db_manager.db 
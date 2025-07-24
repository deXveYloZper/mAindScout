from pymongo import MongoClient
from neo4j import AsyncGraphDatabase, AsyncDriver
from app.core.config import settings
import logging
logger = logging.getLogger(__name__)
class MongoDB:
    client: MongoClient = None
    db = None
class Neo4jDatabase:
    driver: AsyncDriver = None
db_manager = MongoDB()
neo4j_manager = Neo4jDatabase()
async def connect_to_mongo():
    logger.info("Connecting to MongoDB...")
    db_manager.client = MongoClient(settings.MONGODB_URL)
    db_manager.db = db_manager.client[settings.DB_NAME]
    logger.info("MongoDB connection successful.")
async def close_mongo_connection():
    logger.info("Closing MongoDB connection...")
    db_manager.client.close()
    logger.info("MongoDB connection closed.")
async def connect_to_neo4j():
    logger.info("Connecting to Neo4j...")
    neo4j_manager.driver = AsyncGraphDatabase.driver(
        settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
    )
    await neo4j_manager.driver.verify_connectivity()
    logger.info("Neo4j connection successful.")
async def close_neo4j_connection():
    if neo4j_manager.driver:
        await neo4j_manager.driver.close()
        logger.info("Neo4j connection closed.")
def get_database():
    return db_manager.db
def get_neo4j_driver():
    return neo4j_manager.driver 
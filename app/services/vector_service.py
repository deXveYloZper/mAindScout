# app/services/vector_service.py

import logging
from typing import List, Dict, Optional, Tuple
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, 
    Filter, FieldCondition, MatchValue, SearchRequest
)
from qdrant_client.http import models
import numpy as np
from app.core.config import settings
import uuid

logger = logging.getLogger(__name__)


def to_qdrant_id(mongo_id: str) -> str:
    """Deterministically converts a 24-character hex ObjectId string to a UUID string."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, mongo_id))


class VectorService:
    """
    Service for managing vector embeddings in Qdrant vector database.
    Handles storage, retrieval, and similarity search for candidate and job embeddings.
    """
    
    def __init__(self):
        """Initialize Qdrant client and ensure collection exists."""
        self.client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT
        )
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.vector_size = settings.QDRANT_VECTOR_SIZE
        
        # Ensure collection exists
        self._ensure_collection_exists()
        
    def _ensure_collection_exists(self):
        """Create the collection if it doesn't exist."""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Collection {self.collection_name} created successfully")
            else:
                logger.info(f"Collection {self.collection_name} already exists")
                
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {str(e)}")
            raise
    
    def store_candidate_embedding(
        self, 
        candidate_id: str, 
        embedding: List[float], 
        metadata: Dict = None
    ) -> bool:
        """
        Store a candidate's embedding in the vector database.
        
        Args:
            candidate_id: Unique identifier for the candidate
            embedding: Vector embedding (128-dimensional)
            metadata: Additional metadata to store with the embedding
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure embedding is the correct size
            if len(embedding) != self.vector_size:
                raise ValueError(f"Embedding size {len(embedding)} doesn't match expected size {self.vector_size}")
            
            # Prepare metadata
            point_metadata = {
                "candidate_id": candidate_id,
                "type": "candidate",
                **(metadata or {})
            }
            
            # Create point structure
            point = PointStruct(
                id=to_qdrant_id(candidate_id),
                vector=embedding,
                payload=point_metadata
            )
            
            # Upsert the point (insert or update)
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.info(f"Stored candidate embedding for ID: {candidate_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing candidate embedding: {str(e)}")
            return False
    
    def store_job_embedding(
        self, 
        job_id: str, 
        embedding: List[float], 
        metadata: Dict = None
    ) -> bool:
        """
        Store a job description's embedding in the vector database.
        
        Args:
            job_id: Unique identifier for the job
            embedding: Vector embedding (128-dimensional)
            metadata: Additional metadata to store with the embedding
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure embedding is the correct size
            if len(embedding) != self.vector_size:
                raise ValueError(f"Embedding size {len(embedding)} doesn't match expected size {self.vector_size}")
            
            # Prepare metadata
            point_metadata = {
                "job_id": job_id,
                "type": "job",
                **(metadata or {})
            }
            
            # Create point structure
            point = PointStruct(
                id=to_qdrant_id(job_id),
                vector=embedding,
                payload=point_metadata
            )
            
            # Upsert the point (insert or update)
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.info(f"Stored job embedding for ID: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing job embedding: {str(e)}")
            return False
    
    def search_similar_candidates(
        self, 
        job_embedding: List[float], 
        limit: int = 10,
        score_threshold: float = 0.5
    ) -> List[Dict]:
        """
        Search for candidates similar to a job description.
        
        Args:
            job_embedding: Job description embedding
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score threshold
            
        Returns:
            List[Dict]: List of similar candidates with scores
        """
        try:
            # Create filter for candidate type
            candidate_filter = Filter(
                must=[
                    FieldCondition(
                        key="type",
                        match=MatchValue(value="candidate")
                    )
                ]
            )
            
            # Search for similar candidates
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=job_embedding,
                query_filter=candidate_filter,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Format results
            candidates = []
            for result in search_results:
                candidates.append({
                    "candidate_id": result.payload.get("candidate_id"),
                    "similarity_score": result.score,
                    "metadata": result.payload
                })
            
            logger.info(f"Found {len(candidates)} similar candidates")
            return candidates
            
        except Exception as e:
            logger.error(f"Error searching similar candidates: {str(e)}")
            return []
    
    def search_similar_jobs(
        self, 
        candidate_embedding: List[float], 
        limit: int = 10,
        score_threshold: float = 0.5
    ) -> List[Dict]:
        """
        Search for jobs similar to a candidate's profile.
        
        Args:
            candidate_embedding: Candidate profile embedding
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score threshold
            
        Returns:
            List[Dict]: List of similar jobs with scores
        """
        try:
            # Create filter for job type
            job_filter = Filter(
                must=[
                    FieldCondition(
                        key="type",
                        match=MatchValue(value="job")
                    )
                ]
            )
            
            # Search for similar jobs
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=candidate_embedding,
                query_filter=job_filter,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Format results
            jobs = []
            for result in search_results:
                jobs.append({
                    "job_id": result.payload.get("job_id"),
                    "similarity_score": result.score,
                    "metadata": result.payload
                })
            
            logger.info(f"Found {len(jobs)} similar jobs")
            return jobs
            
        except Exception as e:
            logger.error(f"Error searching similar jobs: {str(e)}")
            return []
    
    def get_embedding(self, entity_id: str) -> Optional[List[float]]:
        """
        Retrieve an embedding by entity ID.
        
        Args:
            entity_id: ID of the candidate or job
            
        Returns:
            Optional[List[float]]: The embedding if found, None otherwise
        """
        try:
            points = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[to_qdrant_id(entity_id)]
            )
            
            if points and len(points) > 0:
                return points[0].vector
            else:
                logger.warning(f"No embedding found for entity ID: {entity_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving embedding: {str(e)}")
            return None
    
    def delete_embedding(self, entity_id: str) -> bool:
        """
        Delete an embedding by entity ID.
        
        Args:
            entity_id: ID of the candidate or job to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=[to_qdrant_id(entity_id)]
                )
            )
            
            logger.info(f"Deleted embedding for entity ID: {entity_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting embedding: {str(e)}")
            return False
    
    def get_collection_info(self) -> Dict:
        """
        Get information about the vector collection.
        
        Returns:
            Dict: Collection information including size and configuration
        """
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                "name": collection_info.name,
                "vector_size": collection_info.config.params.vectors.size,
                "distance": collection_info.config.params.vectors.distance,
                "points_count": collection_info.points_count
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {str(e)}")
            return {}
    
    def health_check(self) -> bool:
        """
        Perform a health check on the Qdrant connection.
        
        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            # Try to get collections list
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {str(e)}")
            return False 
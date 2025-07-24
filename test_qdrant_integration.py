# test_qdrant_integration.py

import asyncio
import sys
import os

# Add the core_app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core_app'))

from app.services.vector_service import VectorService
from app.core.config import settings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_qdrant_connection():
    """Test basic Qdrant connection and collection creation."""
    try:
        logger.info("Testing Qdrant connection...")
        vector_service = VectorService()
        
        # Test health check
        if vector_service.health_check():
            logger.info("✅ Qdrant connection successful")
        else:
            logger.error("❌ Qdrant connection failed")
            return False
        
        # Test collection info
        collection_info = vector_service.get_collection_info()
        logger.info(f"Collection info: {collection_info}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing Qdrant connection: {str(e)}")
        return False

def test_embedding_storage():
    """Test storing and retrieving embeddings."""
    try:
        logger.info("Testing embedding storage...")
        vector_service = VectorService()
        
        # Test candidate embedding
        test_candidate_id = "test_candidate_001"
        test_candidate_embedding = [0.1] * 128  # 128-dimensional vector
        
        # Store candidate embedding
        success = vector_service.store_candidate_embedding(
            candidate_id=test_candidate_id,
            embedding=test_candidate_embedding,
            metadata={"name": "Test Candidate", "skills": ["Python", "FastAPI"]}
        )
        
        if success:
            logger.info("✅ Candidate embedding stored successfully")
        else:
            logger.error("❌ Failed to store candidate embedding")
            return False
        
        # Test job embedding
        test_job_id = "test_job_001"
        test_job_embedding = [0.2] * 128  # 128-dimensional vector
        
        # Store job embedding
        success = vector_service.store_job_embedding(
            job_id=test_job_id,
            embedding=test_job_embedding,
            metadata={"title": "Test Job", "company": "Test Company"}
        )
        
        if success:
            logger.info("✅ Job embedding stored successfully")
        else:
            logger.error("❌ Failed to store job embedding")
            return False
        
        # Test retrieval
        retrieved_candidate_embedding = vector_service.get_embedding(test_candidate_id)
        retrieved_job_embedding = vector_service.get_embedding(test_job_id)
        
        if retrieved_candidate_embedding and retrieved_job_embedding:
            logger.info("✅ Embedding retrieval successful")
        else:
            logger.error("❌ Failed to retrieve embeddings")
            return False
        
        # Test similarity search
        similar_candidates = vector_service.search_similar_candidates(
            job_embedding=test_job_embedding,
            limit=5
        )
        
        if similar_candidates:
            logger.info(f"✅ Found {len(similar_candidates)} similar candidates")
            for candidate in similar_candidates:
                logger.info(f"  - Candidate ID: {candidate['candidate_id']}, Score: {candidate['similarity_score']:.3f}")
        else:
            logger.warning("⚠️ No similar candidates found")
        
        # Clean up test data
        vector_service.delete_embedding(test_candidate_id)
        vector_service.delete_embedding(test_job_id)
        logger.info("✅ Test data cleaned up")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing embedding storage: {str(e)}")
        return False

def test_vector_service_methods():
    """Test all vector service methods."""
    try:
        logger.info("Testing vector service methods...")
        vector_service = VectorService()
        
        # Test collection creation
        logger.info("Testing collection creation...")
        # This should be handled by __init__, but let's verify
        
        # Test storing embeddings with different sizes
        logger.info("Testing embedding size validation...")
        
        # Test invalid embedding size
        try:
            vector_service.store_candidate_embedding(
                candidate_id="test_invalid",
                embedding=[0.1] * 64,  # Wrong size
                metadata={}
            )
            logger.error("❌ Should have failed with invalid embedding size")
            return False
        except ValueError:
            logger.info("✅ Correctly rejected invalid embedding size")
        
        # Test valid embeddings
        test_embeddings = [
            ("candidate_1", [0.1] * 128),
            ("candidate_2", [0.2] * 128),
            ("job_1", [0.3] * 128),
            ("job_2", [0.4] * 128)
        ]
        
        for entity_id, embedding in test_embeddings:
            if "candidate" in entity_id:
                success = vector_service.store_candidate_embedding(
                    candidate_id=entity_id,
                    embedding=embedding,
                    metadata={"test": True}
                )
            else:
                success = vector_service.store_job_embedding(
                    job_id=entity_id,
                    embedding=embedding,
                    metadata={"test": True}
                )
            
            if not success:
                logger.error(f"❌ Failed to store {entity_id}")
                return False
        
        logger.info("✅ All test embeddings stored successfully")
        
        # Test search functionality
        logger.info("Testing search functionality...")
        
        # Search for candidates similar to job_1
        similar_candidates = vector_service.search_similar_candidates(
            job_embedding=test_embeddings[2][1],  # job_1 embedding
            limit=10
        )
        
        logger.info(f"Found {len(similar_candidates)} candidates similar to job_1")
        
        # Search for jobs similar to candidate_1
        similar_jobs = vector_service.search_similar_jobs(
            candidate_embedding=test_embeddings[0][1],  # candidate_1 embedding
            limit=10
        )
        
        logger.info(f"Found {len(similar_jobs)} jobs similar to candidate_1")
        
        # Clean up
        for entity_id, _ in test_embeddings:
            vector_service.delete_embedding(entity_id)
        
        logger.info("✅ All test data cleaned up")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing vector service methods: {str(e)}")
        return False

def main():
    """Run all Qdrant integration tests."""
    logger.info("🚀 Starting Qdrant Integration Tests")
    logger.info("=" * 50)
    
    tests = [
        ("Qdrant Connection", test_qdrant_connection),
        ("Embedding Storage", test_embedding_storage),
        ("Vector Service Methods", test_vector_service_methods)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running {test_name} test...")
        try:
            if test_func():
                logger.info(f"✅ {test_name} test PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} test FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} test FAILED with exception: {str(e)}")
    
    logger.info("\n" + "=" * 50)
    logger.info(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Qdrant integration is working correctly.")
        return True
    else:
        logger.error("💥 Some tests failed. Please check the logs above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
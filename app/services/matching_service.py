# app/services/matching_service.py

from app.schemas.candidate_schema import CandidateProfile, CandidateMatch
from app.schemas.job_schema import JobDescription
from app.services.vector_service import VectorService
from app.services.candidate_service import CandidateService
from app.services.job_service import JobService
from typing import List, Dict
import logging
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)

class MatchingService:
    def __init__(
        self,
        candidate_service: CandidateService,
        job_service: JobService,
        vector_service: VectorService
    ):
        self.candidate_service = candidate_service
        self.job_service = job_service
        self.vector_service = vector_service

    async def find_candidates_for_job(self, job_id: str, limit: int = 10) -> List[Dict]:
        """
        Find candidates that match a specific job.
        
        Args:
            job_id: The job ID to find candidates for
            limit: Maximum number of candidates to return
            
        Returns:
            List of candidate matches with scores
        """
        try:
            # Get job embedding
            job_embedding = await self.job_service.get_job_embedding(job_id)
            if not job_embedding:
                logger.warning(f"No embedding found for job {job_id}")
                return []
            
            # Search for similar candidates
            similar_candidates = await run_in_threadpool(
                self.vector_service.search_similar_candidates,
                job_embedding=job_embedding,
                limit=limit
            )
            
            # Enrich with candidate details
            enriched_matches = []
            for match in similar_candidates:
                candidate_id = match["candidate_id"]
                candidate = await self.candidate_service.get_candidate_by_id(candidate_id)
                if candidate:
                    enriched_matches.append({
                        "candidate": candidate,
                        "similarity_score": match["similarity_score"],
                        "metadata": match.get("metadata", {})
                    })
            
            logger.info(f"Found {len(enriched_matches)} candidates for job {job_id}")
            return enriched_matches
            
        except Exception as e:
            logger.error(f"Error finding candidates for job {job_id}: {str(e)}")
            return []

    async def find_jobs_for_candidate(self, candidate_id: str, limit: int = 10) -> List[Dict]:
        """
        Find jobs that match a specific candidate.
        
        Args:
            candidate_id: The candidate ID to find jobs for
            limit: Maximum number of jobs to return
            
        Returns:
            List of job matches with scores
        """
        try:
            # Get candidate embedding
            candidate_embedding = await self.candidate_service.get_candidate_embedding(candidate_id)
            if not candidate_embedding:
                logger.warning(f"No embedding found for candidate {candidate_id}")
                return []
            
            # Search for similar jobs
            similar_jobs = await run_in_threadpool(
                self.vector_service.search_similar_jobs,
                candidate_embedding=candidate_embedding,
                limit=limit
            )
            
            # Enrich with job details
            enriched_matches = []
            for match in similar_jobs:
                job_id = match["job_id"]
                job = await self.job_service.get_job_description(job_id)
                if job:
                    enriched_matches.append({
                        "job": job,
                        "similarity_score": match["similarity_score"],
                        "metadata": match.get("metadata", {})
                    })
            
            logger.info(f"Found {len(enriched_matches)} jobs for candidate {candidate_id}")
            return enriched_matches
            
        except Exception as e:
            logger.error(f"Error finding jobs for candidate {candidate_id}: {str(e)}")
            return []

    async def match_candidates(self, job_description: JobDescription) -> List[CandidateMatch]:
        """
        Match candidates to a job description.
        
        Args:
            job_description: The job description to match against
            
        Returns:
            List of candidate matches
        """
        try:
            # Generate embedding for the job description
            job_embedding = await self.job_service.get_job_embedding(str(job_description.id))
            if not job_embedding:
                logger.warning(f"No embedding found for job {job_description.id}")
                return []
            
            # Find similar candidates
            similar_candidates = await run_in_threadpool(
                self.vector_service.search_similar_candidates,
                job_embedding=job_embedding,
                limit=20
            )
            
            # Convert to CandidateMatch objects
            matches = []
            for match in similar_candidates:
                candidate_id = match["candidate_id"]
                candidate = await self.candidate_service.get_candidate_by_id(candidate_id)
                if candidate:
                    candidate_match = CandidateMatch(
                        candidate=candidate,
                        similarity_score=match["similarity_score"],
                        match_reason="Vector similarity match"
                    )
                    matches.append(candidate_match)
            
            logger.info(f"Generated {len(matches)} matches for job {job_description.id}")
            return matches
            
        except Exception as e:
            logger.error(f"Error matching candidates for job {job_description.id}: {str(e)}")
            return []

    async def get_matched_candidates(self, job_id: str) -> List[CandidateMatch]:
        """
        Get matched candidates for a specific job.
        
        Args:
            job_id: The job ID
            
        Returns:
            List of candidate matches
        """
        try:
            return await self.match_candidates_for_job(job_id)
        except Exception as e:
            logger.error(f"Error getting matched candidates for job {job_id}: {str(e)}")
            return []

    async def match_candidates_for_job(self, job_id: str) -> List[CandidateMatch]:
        """
        Match candidates for a specific job ID.
        
        Args:
            job_id: The job ID
            
        Returns:
            List of candidate matches
        """
        try:
            # Get job details
            job = await self.job_service.get_job_description(job_id)
            if not job:
                logger.warning(f"Job {job_id} not found")
                return []
            
            # Use the existing match_candidates method
            return await self.match_candidates(job)
            
        except Exception as e:
            logger.error(f"Error matching candidates for job {job_id}: {str(e)}")
            return []

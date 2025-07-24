from fastapi import Depends
from pymongo.database import Database
from app.core.database import get_database
from app.core.ml_models import get_embedding_model, get_nlp_model
import spacy
from sentence_transformers import SentenceTransformer

# Import all service classes
from app.services.candidate_service import CandidateService
from app.services.job_service import JobService
from app.services.company_service import CompanyService
from app.services.vector_service import VectorService
from app.services.ontology_service import OntologyService
from app.services.entity_normalization_service import EntityNormalizationService
from app.services.candidate_metrics_service import CandidateMetricsService
from app.services.candidate_evaluation_service import CandidateEvaluationService
from app.services.company_enrichment_service import CompanyEnrichmentService
from app.utils.web_scraper_utils import WebScraperUtil
from app.services.matching_service import MatchingService

# Providers for services with no dependencies

def get_vector_service() -> VectorService:
    return VectorService()

def get_ontology_service() -> OntologyService:
    return OntologyService()

def get_evaluation_service() -> CandidateEvaluationService:
    return CandidateEvaluationService()

# Providers for services with dependencies

def get_entity_normalization_service(
    ontology_service: OntologyService = Depends(get_ontology_service)
) -> EntityNormalizationService:
    return EntityNormalizationService(ontology_service=ontology_service)

def get_metrics_service(
    entity_normalization_service: EntityNormalizationService = Depends(get_entity_normalization_service),
    ontology_service: OntologyService = Depends(get_ontology_service)
) -> CandidateMetricsService:
    return CandidateMetricsService(entity_normalization=entity_normalization_service, ontology_service=ontology_service)

def get_company_service(db: Database = Depends(get_database)) -> CompanyService:
    return CompanyService(db=db)

def get_job_service(
    db: Database = Depends(get_database),
    vector_service: VectorService = Depends(get_vector_service),
    embedding_model: SentenceTransformer = Depends(get_embedding_model),
    nlp_model: spacy.language.Language = Depends(get_nlp_model)
) -> JobService:
    return JobService(
        db=db,
        vector_service=vector_service,
        embedding_model=embedding_model,
        nlp_model=nlp_model
    )

def get_candidate_service(
    db: Database = Depends(get_database),
    vector_service: VectorService = Depends(get_vector_service),
    metrics_service: CandidateMetricsService = Depends(get_metrics_service),
    entity_normalization: EntityNormalizationService = Depends(get_entity_normalization_service),
    embedding_model: SentenceTransformer = Depends(get_embedding_model),
    nlp_model = Depends(get_nlp_model)
) -> CandidateService:
    return CandidateService(
        db=db,
        vector_service=vector_service,
        metrics_service=metrics_service,
        entity_normalization=entity_normalization,
        embedding_model=embedding_model,
        nlp_model=nlp_model
    )

def get_company_enrichment_service(
    db: Database = Depends(get_database),
    scraper: WebScraperUtil = Depends(WebScraperUtil)
) -> CompanyEnrichmentService:
    return CompanyEnrichmentService(db=db, scraper=scraper)

def get_matching_service(
    candidate_service: CandidateService = Depends(get_candidate_service),
    job_service: JobService = Depends(get_job_service),
    vector_service: VectorService = Depends(get_vector_service)
) -> MatchingService:
    return MatchingService(
        candidate_service=candidate_service,
        job_service=job_service,
        vector_service=vector_service
    ) 
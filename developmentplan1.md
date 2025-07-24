Master Recruiter: Development Source of Truth
1.0 Project Vision & Core Mandates
The Master Recruiter application is an AI-powered talent acquisition and business development platform. Its purpose is to automate and scale the functions of an elite agency recruiter.

The system has two core mandates:

Talent Acquisition: Intelligently source, evaluate, and match candidates to open roles with high speed and accuracy.

Business Development: Proactively identify new hiring opportunities (buying signals) in the market and automate data-driven outreach to win new clients.

The entire system is built upon a self-enriching Intelligence Core, which continuously learns from new data to make all functions progressively smarter.

2.0 System Architecture: The Three Pillars
The application is architected around three interconnected pillars:

Pillar I: The Intelligence Core (The "Always-On" Brain)

This foundational layer runs continuously, ingesting and processing all external data (CVs, job postings, company info) to build and enrich the system's proprietary databases. It is responsible for all initial analysis, scoring, and data fusion.

Pillar II: The Reactive Workflow (Filling Open Roles)

This workflow is triggered when a recruiter has a specific job to fill. It leverages the Intelligence Core to find, rank, and present the best-fit candidates from internal and external talent pools.

Pillar III: The Proactive Workflow (Winning New Business)

This workflow runs in the background, constantly monitoring the market for hiring signals. When an opportunity is detected, it automatically identifies the key decision-maker and prepares a personalized, data-backed outreach email.

3.0 Technology Stack
This stack is chosen for performance, scalability, and suitability for AI-driven tasks. All components are compatible and well-supported within the Python ecosystem.

Layer	Technology	Rationale & Compatibility
Core Backend	Python 3.11+, FastAPI	Python is the standard for AI/ML. FastAPI is chosen for its high performance, native async support (critical for I/O-bound API calls), and automatic OpenAPI documentation, making it superior to Flask for modern API development.
Asynchronous Tasks	Celery with Redis Broker	
For handling long-running background jobs (e.g., CV parsing, data enrichment) without blocking the API. This is a standard, robust combination for distributed task queues.   

Primary Database	MongoDB	
Its flexible, document-oriented model is ideal for storing the semi-structured and varied data extracted from resumes and company profiles.   

Vector Database	Qdrant	A high-performance vector database required for storing text embeddings and enabling fast, large-scale semantic similarity search, which is the core of our matching engine.
Knowledge Graph	Neo4j	Purpose-built for modeling the complex relationships between skills, companies, and job titles. This forms the backbone of our skills ontology and advanced intelligence features.
NLP & ML	spaCy, sentence-transformers, LightGBM	spaCy is chosen over NLTK for its production-grade performance and superior custom NER training capabilities. sentence-transformers simplifies the creation of state-of-the-art text embeddings from BERT-like models. LightGBM is a fast, efficient gradient boosting framework for the Learning-to-Rank model, often outperforming XGBoost.
Frontend	React	A flexible and powerful library with a vast ecosystem, ideal for building the complex, data-intensive user interfaces required for this platform.
Key Integrations	Crunchbase, BuiltWith, LinkedIn API, Clearout	
APIs for enriching company profiles with firmographic , technographic , and contact data. Clearout will be used for email verification.   

4.0 Phased Development Plan
This plan breaks down the project into four logical phases. Each step includes the module to be built, implementation details, dependencies, and a clear validation goal.

Phase 1: The Foundation – Candidate Data Core (MVP)
Objective: Build the core pipeline to ingest, parse, and store a single CV.

Step	Action / Module	Description & Implementation Details	Dependencies	Test & Validation Goal
1.1	Setup: Project & Databases	Initialize a Python project with FastAPI. Set up instances for MongoDB, Qdrant, and Neo4j. Configure environment variables for database connections.	None	Project structure is created. All database instances are running and accessible.
1.2	Module: cv_ingestion_service	Create a FastAPI endpoint (/upload/cv/) that accepts file uploads (PDF, DOCX). This service will handle the initial file reception and storage.	Project Setup (1.1)	A user can successfully POST a PDF or DOCX file to the endpoint.
1.3	Module: text_extraction_service	Create a Python module that takes a file path as input. Use pdfminer.six for PDFs and python-docx2txt for DOCX files to extract raw text. Implement a fallback mechanism. The function should return a clean string.	cv_ingestion_service (1.2)	A CV file is successfully converted into a clean, raw text string.
1.4	Module: basic_parsing_service	
Create a V1 parser. This module uses Regular Expressions to extract well-defined patterns like email and phone numbers. Use a pre-trained spaCy model (en_core_web_lg) to extract generic entities like PERSON and GPE.   

text_extraction_service (1.3)	Given raw text, the module outputs a JSON object with basic extracted entities.
1.5	Module: database_persistence_service	Develop a service to connect to MongoDB. It will take the JSON output from the parser and save it to a candidates collection based on the schema defined in Section 5.0.	basic_parsing_service (1.4)	A parsed CV's structured data is correctly stored in the MongoDB candidates collection.
1.6	End-to-End Test	Create a simple test script or use FastAPI's interactive docs to upload a CV and verify that the structured data appears correctly in the MongoDB database.	All Phase 1 steps	Phase 1 Complete: The core data ingestion pipeline is functional from file upload to database storage.
Phase 2: Intelligence Enhancement – Building the Brain
Objective: Evolve from a basic parser to an intelligent system with custom models and enriched data.

Step	Action / Module	Description & Implementation Details	Dependencies	Test & Validation Goal
2.1	Task: Data Annotation	
Set up Doccano. Begin annotating a corpus of ~200-500 resumes with custom labels: SKILL, JOB_TITLE, DEGREE, UNIVERSITY, COMPANY_NAME. Use existing datasets like the one on Kaggle for a head start.   

None	
A high-quality, annotated dataset is created in the spaCy JSON format.   

2.2	Task: Custom NER Model Training	
Create a spaCy v3 training pipeline using a config.cfg file. Fine-tune a pre-trained model (e.g.,    

en_core_web_lg) on the annotated dataset from Step 2.1 to prevent "catastrophic forgetting".   

Annotated Data (2.1)	A trained, saved custom NER model file (model-best) is produced.
2.3	Module: advanced_parsing_service	Replace the basic_parsing_service (1.4) with the new custom NER model. This service will now accurately extract domain-specific entities from CVs and Job Descriptions.	Custom NER Model (2.2)	Parsing a CV yields a rich JSON with specific, accurate labels (e.g., {"skills":, "job_title": "Software Engineer"}).
2.4	Module: ontology_service	Design and implement the skills/job title ontology in Neo4j. Create nodes for Skill and JobTitle and relationships like IS_A, ALIAS_OF. Populate it with an initial list of common skills and titles. Use the neo4j-driver for Python.	Neo4j Setup (1.1)	A queryable knowledge graph of skills and job titles is available.
2.5	Module: entity_normalization_service	Create a service that runs after the advanced_parsing_service (2.3). It queries the ontology_service (2.4) to map extracted strings (e.g., "SDE") to their canonical IDs before database persistence.	advanced_parsing_service (2.3), ontology_service (2.4)	Data stored in MongoDB is clean and standardized.
2.6	Module: company_enrichment_service	This is a Celery background task. When a new company is parsed, this service is triggered. It uses APIs from Crunchbase (firmographics) and BuiltWith (technographics) to fetch additional data.	Celery/Redis Setup	A company profile in MongoDB is enriched with external data.
2.7	Logic: Data Fusion	Within the company_enrichment_service, implement a rule-based data fusion model. Define a source trust score (e.g., API data > CV data) and use recency weighting to resolve data conflicts and create a "golden record".	company_enrichment_service (2.6)	Phase 2 Complete: The system contains deeply structured, normalized, and enriched profiles for candidates and companies.
Phase 3: Core Functionality – The Matching & Ranking Engine
Objective: Build the primary recruiter workflow for matching candidates to jobs.

Step	Action / Module	Description & Implementation Details	Dependencies	Test & Validation Goal
3.1	Module: jd_parser_service	
Create an API endpoint (/parse/jd/) that accepts job description text. This service reuses the advanced_parsing_service (2.3) to extract structured requirements (skills, experience years, etc.) from the JD.   

advanced_parsing_service (2.3)	Pasting a JD results in a structured JSON of its requirements.
3.2	Module: candidate_metrics_service	A service (likely a Celery task triggered on new CV ingestion) that calculates and stores derived metrics on the candidate profile in MongoDB. Implement the logic from Section 7.1 to calculate relevant_experience_years and average_tenure_months.	Enriched Candidate Data (Phase 2)	Candidate profiles in MongoDB are updated with calculated metrics.
3.3	Module: universal_scoring_service	A service that calculates the Universal_Profile_Score for each candidate based on the logic in Section 7.2. This score should be stored in the candidate's MongoDB document.	candidate_metrics_service (3.2)	Every candidate in the database has a baseline quality score.
3.4	Module: semantic_embedding_service	A Celery task that uses the sentence-transformers library to generate vector embeddings for the text of all CVs and incoming JDs. Store these embeddings in the Qdrant vector database, linked by candidate/job ID.	advanced_parsing_service (2.3)	All CVs and JDs have corresponding vector embeddings stored in Qdrant.
3.5	Module: matching_service	Create an endpoint (/match/job/{job_id}) that orchestrates the matching. It fetches the JD, queries Qdrant for the top N semantically similar candidates, and then calculates the final Hybrid_Match_Score for each using the logic from Section 7.3.	All previous Phase 3 steps	The endpoint returns a ranked list of candidate IDs and their match scores for a given job.
3.6	UI: Recruiter Workflow	Develop the frontend React application. Create a page to input a new job and a results page that calls the /match/job/{job_id} endpoint and displays the ranked list of candidates with their scores.	matching_service (3.5)	A recruiter can enter a job and see a ranked list of candidates.
3.7	UI: Explainable AI (XAI) Panel	In the results UI, for each candidate, display a breakdown of why they received their score (e.g., "Skills Match: 9/10", "Semantic Fit: 8.5/10"). This data should be provided by the matching_service.	matching_service (3.5)	Phase 3 Complete: The core product is functional. Recruiters can match jobs to candidates and understand the reasoning.
Phase 4: Proactive Growth – The Business Development Engine
Objective: Build the advanced, outward-facing features for sourcing and winning new business.

Step	Action / Module	Description & Implementation Details	Dependencies	Test & Validation Goal
4.1	Module: learning_to_rank_service	Implement a feedback loop in the UI to track recruiter actions (e.g., shortlisting, rejecting). Use this data to train a LightGBM LTR model that re-ranks the initial shortlist from the matching_service.	Ranked Results (Phase 3)	Candidate ranking becomes more personalized and accurate over time.
4.2	Module: buying_signal_monitor	
A scheduled Celery task that continuously monitors external sources for hiring-related "buying signals". It scrapes key job boards for new postings and uses the    

Crunchbase API for funding/leadership change alerts.	Company Intelligence Engine (Phase 2)	The system generates a real-time feed of new business opportunities.
4.3	Module: prospect_identification_service	When a new job opening is detected, this service attempts to identify the hiring manager using a waterfall logic: 1) Analyze JD text. 2) Query internal company data. 3) Use LinkedIn search patterns. 4) Use Clearout API for email verification.	buying_signal_monitor (4.2)	For a given job opening, the system suggests a probable hiring manager's contact info.
4.4	Module: speculative_outreach_engine	This service connects all the pieces. When a buying signal is detected, it automatically: 1) Runs the JD through the matching_service to find the top candidates. 2) Calls the prospect_identification_service. 3) Populates a pre-written email template with all relevant details.	All previous steps	Phase 4 Complete: The system can autonomously identify a new business opportunity and prepare a high-quality, data-backed "spec email" for the recruiter to review and send.
5.0 Data Models & Schemas (MongoDB)
5.1 candidates Collection Schema
JSON

{
  "_id": "ObjectId",
  "candidate_id": "string (UUID)",
  "contact_info": {
    "name": "string",
    "email": "string",
    "phone": "string",
    "location_city": "string",
    "location_country": "string",
    "social_links": ["string"]
  },
  "education": [
    {
      "degree": "string",
      "major": "string",
      "school_name": "string",
      "school_id": "ObjectId (ref: companies)",
      "graduation_year": "integer"
    }
  ],
  "work_experience":"
    }
  ],
  "skills": [
    {
      "skill_name": "string",
      "skill_id": "string (ref: ontology)"
    }
  ],
  "derived_metrics": {
    "total_experience_years": "float",
    "relevant_experience_years": "float",
    "average_tenure_months": "float",
    "universal_profile_score": "float",
    "seniority_level": "string (Junior/Mid/Senior)"
  },
  "metadata": {
    "source_file_path": "string",
    "created_at": "Timestamp",
    "last_updated": "Timestamp"
  }
}
5.2 companies Collection Schema
JSON

{
  "_id": "ObjectId",
  "company_id": "string (UUID)",
  "company_name": "string",
  "domains": ["string"],
  "description": "string",
  "firmographics": {
    "industry": "string",
    "employee_count": "integer",
    "annual_revenue": "integer",
    "founding_year": "integer",
    "locations": ["string"]
  },
  "technographics": {
    "tech_stack": ["string"]
  },
  "funding_history":,
  "metadata": {
    "source": "string (e.g., 'Crunchbase API', 'CV Parse')",
    "last_updated": "Timestamp"
  }
}
6.0 Key Algorithms & Logic
6.1 Relevant Experience Calculation
Define keyword sets for professional domains (e.g., Software Development: {'developer', 'engineer', 'sde'}).

Iterate through the candidate's work_experience array.

For each job, check if its job_title contains any keywords from the target domain.

Sum the duration_months for all matched jobs to get relevant_experience_years.

6.2 Universal Candidate Score Calculation
This score is a weighted sum of several sub-scores, with weights adjusted by seniority_level.

Universal Score = w_exp * Score_exp + w_stab * Score_stab + w_prog * Score_prog + w_pres * Score_pres

Score_exp: Based on relevant_experience_years.

Score_stab: Based on average_tenure_months.

Score_prog: Algorithmically assesses career growth by analyzing the sequence of job_title_ids over time against the Neo4j ontology.

Score_pres: Based on the tier/prestige of companies in the work history, as determined by the Company Intelligence Engine.

6.3 Hybrid Match Score Calculation
This score combines structured and semantic matching.

Match Score = w_sem * S_sem + w_skill * S_skill + w_exp * S_exp + w_loc * S_loc

S_sem: Cosine similarity score from Qdrant vector search.

S_skill: Percentage of mandatory skills from the JD present in the candidate's profile.

S_exp: Score based on whether relevant_experience_years meets the JD requirement.

S_loc: Score based on location match.

Weights (w_...) are configurable per job to prioritize different factors.

7.0 Final Development Notes
Configuration Management: All API keys, database credentials, and model parameters should be managed via environment variables, not hardcoded.

Logging: Implement comprehensive logging in all services to facilitate debugging and monitoring.

Bias Mitigation: The performance of all AI models is contingent on the quality and fairness of the input data. Regularly audit training data and model outputs for potential bias. The XAI panel is a key feature for ensuring transparency and allowing human oversight.

Testing: Write unit tests for individual functions and integration tests for entire workflows to ensure reliability.
# app/services/ontology_service.py

import logging
from typing import List, Dict, Optional
from neo4j import AsyncGraphDatabase, AsyncDriver
import os
import json

logger = logging.getLogger(__name__)

class OntologyService:
    """
    Service for managing and querying the Neo4j knowledge graph.
    Handles entity normalization for skills and job titles.
    This version is refactored to be fully asynchronous and non-blocking.
    """

    def __init__(self, driver: AsyncDriver):
        """
        Initialize the service with a shared, asynchronous Neo4j driver.
        The driver is now injected as a dependency instead of being created here.
        """
        self.driver = driver

    async def ensure_schema_exists(self):
        """
        Ensure all necessary unique constraints and indexes exist in the Neo4j database.
        This is an idempotent operation, safe to run on startup.
        """
        async with self.driver.session() as session:
            try:
                await session.run("CREATE CONSTRAINT skill_id_unique IF NOT EXISTS FOR (s:Skill) REQUIRE s.id IS UNIQUE")
                await session.run("CREATE CONSTRAINT skill_name_unique IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE")
                await session.run("CREATE CONSTRAINT job_title_id_unique IF NOT EXISTS FOR (j:JobTitle) REQUIRE j.id IS UNIQUE")
                await session.run("CREATE CONSTRAINT job_title_name_unique IF NOT EXISTS FOR (j:JobTitle) REQUIRE j.name IS UNIQUE")
                await session.run("CREATE CONSTRAINT alias_name_unique IF NOT EXISTS FOR (a:Alias) REQUIRE a.name IS UNIQUE")
                logger.info("Neo4j schema constraints and indexes verified.")
            except Exception as e:
                logger.error(f"Error creating Neo4j schema: {e}")
                raise

    async def load_initial_data_if_empty(self):
        """
        Check if the ontology is empty and, if so, populate it with initial data
        from the skills_taxonomy.json file.
        """
        async with self.driver.session() as session:
            result = await session.run("MATCH (s:Skill) RETURN count(s) as count")
            record = await result.single()
            skill_count = record["count"] if record else 0

            if skill_count == 0:
                logger.info("Ontology is empty. Loading initial skills data...")
                await self._load_skills_from_taxonomy(session)

    async def _load_skills_from_taxonomy(self, session):
        """Helper method to load skills from the JSON taxonomy file."""
        try:
            taxonomy_path = os.path.join('app', 'data', 'skills_taxonomy.json')
            with open(taxonomy_path, 'r', encoding='utf-8') as f:
                skills_taxonomy = json.load(f)

            for alias, canonical in skills_taxonomy.items():
                # This query creates the canonical skill if it doesn't exist,
                # creates the alias if it doesn't exist,
                # and ensures the relationship between them exists.
                await session.run(
                    """
                    MERGE (s:Skill {name: $canonical})
                    ON CREATE SET s.id = apoc.create.uuid()
                    MERGE (a:Alias {name: $alias})
                    MERGE (a)-[:ALIAS_OF]->(s)
                    """,
                    canonical=canonical, alias=alias.lower()
                )
            logger.info(f"Loaded {len(skills_taxonomy)} skills into ontology.")
        except Exception as e:
            logger.error(f"Error loading skills from taxonomy: {e}")

    async def normalize_skill(self, skill_name: str) -> Optional[str]:
        """
        Normalize a skill name to its canonical form using the knowledge graph.
        """
        async with self.driver.session() as session:
            result = await session.run(
                "MATCH (a:Alias {name: $skill_name})-[:ALIAS_OF]->(s:Skill) RETURN s.name as canonical_name LIMIT 1",
                skill_name=skill_name.lower()
            )
            record = await result.single()
            return record["canonical_name"] if record else None

    async def normalize_job_title(self, job_title: str) -> Optional[str]:
        """
        Normalize a job title to its canonical form using the knowledge graph.
        """
        async with self.driver.session() as session:
            result = await session.run(
                "MATCH (a:Alias {name: $job_title})-[:ALIAS_OF]->(j:JobTitle) RETURN j.name as canonical_name LIMIT 1",
                job_title=job_title.lower()
            )
            record = await result.single()
            return record["canonical_name"] if record else None

    async def get_related_skills(self, skill_name: str, max_depth: int = 2) -> List[str]:
        """
        Get skills related to a given skill up to a certain depth in the graph.
        """
        async with self.driver.session() as session:
            query = """
            MATCH (start_skill:Skill {name: $skill_name})
            MATCH path = (start_skill)-[:RELATED_TO*1..%d]-(related_skill:Skill)
            RETURN DISTINCT related_skill.name AS related_skill
            """ % max_depth
            result = await session.run(query, skill_name=skill_name)
            return [record["related_skill"] for record in await result.list()]

    async def add_skill_alias(self, canonical_name: str, alias_name: str) -> bool:
        """Add a new alias for an existing skill."""
        async with self.driver.session() as session:
            await session.run(
                """
                MERGE (s:Skill {name: $canonical})
                MERGE (a:Alias {name: $alias})
                MERGE (a)-[:ALIAS_OF]->(s)
                """,
                canonical=canonical_name, alias=alias_name.lower()
            )
            return True

    async def add_job_title_alias(self, canonical_name: str, alias_name: str) -> bool:
        """Add a new alias for an existing job title."""
        async with self.driver.session() as session:
            await session.run(
                """
                MERGE (j:JobTitle {name: $canonical})
                MERGE (a:Alias {name: $alias})
                MERGE (a)-[:ALIAS_OF]->(j)
                """,
                canonical=canonical_name, alias=alias_name.lower()
            )
            return True

    async def health_check(self) -> bool:
        """Perform a health check on the Neo4j connection."""
        try:
            await self.driver.verify_connectivity()
            return True
        except Exception as e:
            logger.error(f"Neo4j health check failed: {str(e)}")
            return False

    async def close(self):
        """Close the Neo4j driver connection."""
        if self.driver:
            await self.driver.close()
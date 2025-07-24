# app/services/ontology_service.py

import logging
from typing import List, Dict, Optional, Set
from neo4j import GraphDatabase
from app.core.config import settings
import os
import json

logger = logging.getLogger(__name__)


class OntologyService:
    """
    Service for managing the Neo4j knowledge graph ontology.
    Handles skills and job title relationships, entity normalization, and canonical ID mapping.
    """
    
    def __init__(self):
        """Initialize Neo4j driver and ensure database schema exists."""
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        
        # Ensure schema exists
        self._ensure_schema_exists()
        
        # Load initial data if database is empty
        self._load_initial_data()
    
    def _ensure_schema_exists(self):
        """Create constraints and indexes for the ontology."""
        try:
            with self.driver.session() as session:
                # Create constraints for unique properties
                session.run("CREATE CONSTRAINT skill_id_unique IF NOT EXISTS FOR (s:Skill) REQUIRE s.id IS UNIQUE")
                session.run("CREATE CONSTRAINT job_title_id_unique IF NOT EXISTS FOR (j:JobTitle) REQUIRE j.id IS UNIQUE")
                session.run("CREATE CONSTRAINT skill_name_unique IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE")
                session.run("CREATE CONSTRAINT job_title_name_unique IF NOT EXISTS FOR (j:JobTitle) REQUIRE j.name IS UNIQUE")
                
                # Create indexes for performance
                session.run("CREATE INDEX skill_aliases IF NOT EXISTS FOR (s:Skill) ON (s.aliases)")
                session.run("CREATE INDEX job_title_aliases IF NOT EXISTS FOR (j:JobTitle) ON (j.aliases)")
                
                logger.info("Neo4j schema constraints and indexes created successfully")
                
        except Exception as e:
            logger.error(f"Error creating schema: {str(e)}")
            raise
    
    def _load_initial_data(self):
        """Load initial skills and job titles from taxonomy files."""
        try:
            # Check if data already exists
            with self.driver.session() as session:
                result = session.run("MATCH (s:Skill) RETURN count(s) as count")
                skill_count = result.single()["count"]
                
                if skill_count == 0:
                    logger.info("Loading initial skills data...")
                    self._load_skills_from_taxonomy()
                
                result = session.run("MATCH (j:JobTitle) RETURN count(j) as count")
                job_count = result.single()["count"]
                
                if job_count == 0:
                    logger.info("Loading initial job titles data...")
                    self._load_job_titles_from_taxonomy()
                    
        except Exception as e:
            logger.error(f"Error loading initial data: {str(e)}")
    
    def _load_skills_from_taxonomy(self):
        """Load skills from the existing taxonomy file."""
        try:
            taxonomy_path = os.path.join('app', 'data', 'skills_taxonomy.json')
            with open(taxonomy_path, 'r', encoding='utf-8') as f:
                skills_taxonomy = json.load(f)
            
            with self.driver.session() as session:
                for skill_alias, canonical_name in skills_taxonomy.items():
                    # Create or merge the canonical skill
                    session.run("""
                        MERGE (s:Skill {name: $canonical_name})
                        SET s.id = $skill_id,
                            s.category = $category,
                            s.aliases = $aliases
                    """, {
                        'canonical_name': canonical_name,
                        'skill_id': f"skill_{canonical_name.lower().replace(' ', '_')}",
                        'category': 'technology',
                        'aliases': [skill_alias.lower()]
                    })
                    
                    # Create alias relationship
                    session.run("""
                        MATCH (s:Skill {name: $canonical_name})
                        MERGE (a:Alias {name: $alias_name})
                        MERGE (a)-[:ALIAS_OF]->(s)
                    """, {
                        'canonical_name': canonical_name,
                        'alias_name': skill_alias.lower()
                    })
            
            logger.info(f"Loaded {len(skills_taxonomy)} skills into ontology")
            
        except Exception as e:
            logger.error(f"Error loading skills from taxonomy: {str(e)}")
    
    def _load_job_titles_from_taxonomy(self):
        """Load common job titles into the ontology."""
        try:
            # Common tech job titles with aliases
            job_titles = {
                "Software Engineer": ["swe", "software developer", "developer", "programmer", "coder"],
                "Senior Software Engineer": ["senior developer", "senior swe", "lead developer"],
                "Full Stack Developer": ["fullstack developer", "full-stack developer", "full stack engineer"],
                "Frontend Developer": ["front-end developer", "front end developer", "ui developer"],
                "Backend Developer": ["back-end developer", "back end developer", "server developer"],
                "DevOps Engineer": ["devops", "site reliability engineer", "sre"],
                "Data Scientist": ["data analyst", "ml engineer", "machine learning engineer"],
                "Product Manager": ["pm", "product owner", "technical product manager"],
                "QA Engineer": ["quality assurance engineer", "test engineer", "software tester"],
                "System Administrator": ["sysadmin", "system admin", "it administrator"],
                "Database Administrator": ["dba", "database admin", "db administrator"],
                "Network Engineer": ["network admin", "network administrator"],
                "Security Engineer": ["security analyst", "cybersecurity engineer", "infosec engineer"],
                "Cloud Engineer": ["cloud architect", "aws engineer", "azure engineer"],
                "Mobile Developer": ["ios developer", "android developer", "mobile app developer"]
            }
            
            with self.driver.session() as session:
                for canonical_title, aliases in job_titles.items():
                    # Create or merge the canonical job title
                    session.run("""
                        MERGE (j:JobTitle {name: $canonical_name})
                        SET j.id = $job_id,
                            j.category = $category,
                            j.aliases = $aliases
                    """, {
                        'canonical_name': canonical_title,
                        'job_id': f"job_{canonical_title.lower().replace(' ', '_')}",
                        'category': 'engineering',
                        'aliases': [alias.lower() for alias in aliases]
                    })
                    
                    # Create alias relationships
                    for alias in aliases:
                        session.run("""
                            MATCH (j:JobTitle {name: $canonical_name})
                            MERGE (a:Alias {name: $alias_name})
                            MERGE (a)-[:ALIAS_OF]->(j)
                        """, {
                            'canonical_name': canonical_title,
                            'alias_name': alias.lower()
                        })
            
            logger.info(f"Loaded {len(job_titles)} job titles into ontology")
            
        except Exception as e:
            logger.error(f"Error loading job titles: {str(e)}")
    
    def normalize_skill(self, skill_name: str) -> Optional[str]:
        """
        Normalize a skill name to its canonical form.
        
        Args:
            skill_name: The skill name to normalize
            
        Returns:
            Optional[str]: The canonical skill name if found, None otherwise
        """
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (a:Alias {name: $skill_name})-[:ALIAS_OF]->(s:Skill)
                    RETURN s.name as canonical_name
                    LIMIT 1
                """, {'skill_name': skill_name.lower()})
                
                record = result.single()
                if record:
                    return record["canonical_name"]
                
                # Try direct match
                result = session.run("""
                    MATCH (s:Skill {name: $skill_name})
                    RETURN s.name as canonical_name
                    LIMIT 1
                """, {'skill_name': skill_name})
                
                record = result.single()
                return record["canonical_name"] if record else None
                
        except Exception as e:
            logger.error(f"Error normalizing skill {skill_name}: {str(e)}")
            return None
    
    def normalize_job_title(self, job_title: str) -> Optional[str]:
        """
        Normalize a job title to its canonical form.
        
        Args:
            job_title: The job title to normalize
            
        Returns:
            Optional[str]: The canonical job title if found, None otherwise
        """
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (a:Alias {name: $job_title})-[:ALIAS_OF]->(j:JobTitle)
                    RETURN j.name as canonical_name
                    LIMIT 1
                """, {'job_title': job_title.lower()})
                
                record = result.single()
                if record:
                    return record["canonical_name"]
                
                # Try direct match
                result = session.run("""
                    MATCH (j:JobTitle {name: $job_title})
                    RETURN j.name as canonical_name
                    LIMIT 1
                """, {'job_title': job_title})
                
                record = result.single()
                return record["canonical_name"] if record else None
                
        except Exception as e:
            logger.error(f"Error normalizing job title {job_title}: {str(e)}")
            return None
    
    def get_skill_aliases(self, canonical_skill: str) -> List[str]:
        """
        Get all aliases for a canonical skill.
        
        Args:
            canonical_skill: The canonical skill name
            
        Returns:
            List[str]: List of aliases
        """
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (s:Skill {name: $skill_name})
                    OPTIONAL MATCH (a:Alias)-[:ALIAS_OF]->(s)
                    RETURN collect(a.name) as aliases
                """, {'skill_name': canonical_skill})
                
                record = result.single()
                return record["aliases"] if record and record["aliases"] else []
                
        except Exception as e:
            logger.error(f"Error getting aliases for skill {canonical_skill}: {str(e)}")
            return []
    
    def get_job_title_aliases(self, canonical_job_title: str) -> List[str]:
        """
        Get all aliases for a canonical job title.
        
        Args:
            canonical_job_title: The canonical job title
            
        Returns:
            List[str]: List of aliases
        """
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (j:JobTitle {name: $job_title})
                    OPTIONAL MATCH (a:Alias)-[:ALIAS_OF]->(j)
                    RETURN collect(a.name) as aliases
                """, {'job_title': canonical_job_title})
                
                record = result.single()
                return record["aliases"] if record and record["aliases"] else []
                
        except Exception as e:
            logger.error(f"Error getting aliases for job title {canonical_job_title}: {str(e)}")
            return []
    
    def add_skill_alias(self, canonical_skill: str, alias: str) -> bool:
        """
        Add a new alias for an existing skill.
        
        Args:
            canonical_skill: The canonical skill name
            alias: The new alias to add
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.driver.session() as session:
                session.run("""
                    MATCH (s:Skill {name: $canonical_name})
                    MERGE (a:Alias {name: $alias_name})
                    MERGE (a)-[:ALIAS_OF]->(s)
                """, {
                    'canonical_name': canonical_skill,
                    'alias_name': alias.lower()
                })
                
                logger.info(f"Added alias '{alias}' for skill '{canonical_skill}'")
                return True
                
        except Exception as e:
            logger.error(f"Error adding skill alias: {str(e)}")
            return False
    
    def add_job_title_alias(self, canonical_job_title: str, alias: str) -> bool:
        """
        Add a new alias for an existing job title.
        
        Args:
            canonical_job_title: The canonical job title
            alias: The new alias to add
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.driver.session() as session:
                session.run("""
                    MATCH (j:JobTitle {name: $canonical_name})
                    MERGE (a:Alias {name: $alias_name})
                    MERGE (a)-[:ALIAS_OF]->(j)
                """, {
                    'canonical_name': canonical_job_title,
                    'alias_name': alias.lower()
                })
                
                logger.info(f"Added alias '{alias}' for job title '{canonical_job_title}'")
                return True
                
        except Exception as e:
            logger.error(f"Error adding job title alias: {str(e)}")
            return False
    
    def create_skill_relationship(self, skill1: str, skill2: str, relationship_type: str) -> bool:
        """
        Create a relationship between two skills.
        
        Args:
            skill1: First skill name
            skill2: Second skill name
            relationship_type: Type of relationship (e.g., "IS_A", "RELATED_TO", "PREREQUISITE")
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.driver.session() as session:
                session.run("""
                    MATCH (s1:Skill {name: $skill1})
                    MATCH (s2:Skill {name: $skill2})
                    MERGE (s1)-[r:RELATED_TO]->(s2)
                    SET r.type = $relationship_type
                """, {
                    'skill1': skill1,
                    'skill2': skill2,
                    'relationship_type': relationship_type
                })
                
                logger.info(f"Created {relationship_type} relationship between '{skill1}' and '{skill2}'")
                return True
                
        except Exception as e:
            logger.error(f"Error creating skill relationship: {str(e)}")
            return False
    
    def get_related_skills(self, skill_name: str, max_depth: int = 2) -> List[Dict]:
        """
        Get skills related to a given skill.
        
        Args:
            skill_name: The skill name
            max_depth: Maximum depth of relationships to traverse
            
        Returns:
            List[Dict]: List of related skills with relationship information
        """
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (s:Skill {name: $skill_name})-[r:RELATED_TO*1..$max_depth]-(related:Skill)
                    RETURN related.name as name, 
                           related.category as category,
                           length(r) as distance
                    ORDER BY distance
                """, {
                    'skill_name': skill_name,
                    'max_depth': max_depth
                })
                
                return [record.data() for record in result]
                
        except Exception as e:
            logger.error(f"Error getting related skills for {skill_name}: {str(e)}")
            return []
    
    def health_check(self) -> bool:
        """
        Perform a health check on the Neo4j connection.
        
        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                return result.single()["test"] == 1
        except Exception as e:
            logger.error(f"Neo4j health check failed: {str(e)}")
            return False
    
    def close(self):
        """Close the Neo4j driver connection."""
        self.driver.close() 
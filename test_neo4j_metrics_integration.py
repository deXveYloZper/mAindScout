#!/usr/bin/env python3
"""
Test script for Neo4j Knowledge Graph, Entity Normalization, and Candidate Metrics Integration
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the core_app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core_app'))

from app.services.ontology_service import OntologyService
from app.services.entity_normalization_service import EntityNormalizationService
from app.services.candidate_metrics_service import CandidateMetricsService
from app.core.config import settings

def test_ontology_service():
    """Test the Neo4j ontology service."""
    print("🔍 Testing Neo4j Ontology Service...")
    
    try:
        # Initialize ontology service
        ontology = OntologyService()
        
        # Test health check
        health_status = ontology.health_check()
        print(f"✅ Neo4j Health Check: {'PASSED' if health_status else 'FAILED'}")
        
        if not health_status:
            print("❌ Neo4j connection failed. Please ensure Neo4j is running.")
            return False
        
        # Test skill normalization
        test_skills = ["python", "javascript", "react", "aws", "docker", "unknown_skill"]
        print("\n🧪 Testing Skill Normalization:")
        
        for skill in test_skills:
            canonical = ontology.normalize_skill(skill)
            print(f"  {skill} -> {canonical or 'Not found'}")
        
        # Test job title normalization
        test_titles = ["software engineer", "swe", "senior developer", "devops", "unknown_title"]
        print("\n🧪 Testing Job Title Normalization:")
        
        for title in test_titles:
            canonical = ontology.normalize_job_title(title)
            print(f"  {title} -> {canonical or 'Not found'}")
        
        # Test adding custom mappings
        print("\n🧪 Testing Custom Mapping Addition:")
        success = ontology.add_skill_alias("Python", "py")
        print(f"  Added 'py' -> 'Python': {'SUCCESS' if success else 'FAILED'}")
        
        # Test the new mapping
        canonical = ontology.normalize_skill("py")
        print(f"  'py' -> {canonical or 'Not found'}")
        
        ontology.close()
        return True
        
    except Exception as e:
        print(f"❌ Ontology Service Test Failed: {str(e)}")
        return False

def test_entity_normalization_service():
    """Test the entity normalization service."""
    print("\n🔍 Testing Entity Normalization Service...")
    
    try:
        # Initialize entity normalization service
        entity_norm = EntityNormalizationService()
        
        # Test skill normalization with fuzzy matching
        test_skills = ["python", "javascript", "react", "aws", "docker", "unknown_skill", "py"]
        print("\n🧪 Testing Skill Normalization with Fuzzy Matching:")
        
        normalized_skills = entity_norm.normalize_skills(test_skills, fuzzy_threshold=80.0)
        
        for skill_data in normalized_skills:
            print(f"  {skill_data['original']} -> {skill_data['canonical']} "
                  f"(confidence: {skill_data['confidence']:.2f}, type: {skill_data['match_type']})")
        
        # Test job title normalization
        test_titles = ["software engineer", "swe", "senior developer", "devops", "unknown_title"]
        print("\n🧪 Testing Job Title Normalization:")
        
        normalized_titles = entity_norm.normalize_job_titles(test_titles, fuzzy_threshold=80.0)
        
        for title_data in normalized_titles:
            print(f"  {title_data['original']} -> {title_data['canonical']} "
                  f"(confidence: {title_data['confidence']:.2f}, type: {title_data['match_type']})")
        
        # Test work experience normalization
        test_work_exp = [
            {
                "company": "Google Inc.",
                "title": "Software Engineer",
                "start_date": "2020-01-01",
                "end_date": "2023-06-30",
                "responsibilities": ["Developed Python applications", "Used React for frontend"]
            },
            {
                "company": "Startup XYZ",
                "title": "Senior Developer",
                "start_date": "2018-03-01",
                "end_date": "2019-12-31",
                "responsibilities": ["Led JavaScript development", "Implemented AWS solutions"]
            }
        ]
        
        print("\n🧪 Testing Work Experience Normalization:")
        normalized_exp = entity_norm.normalize_work_experience(test_work_exp)
        
        for i, exp in enumerate(normalized_exp):
            print(f"  Experience {i+1}:")
            print(f"    Company: {exp.get('company')} -> {exp.get('canonical_company')}")
            print(f"    Title: {exp.get('title')} -> {exp.get('canonical_title')} "
                  f"(confidence: {exp.get('title_confidence', 0):.2f})")
            if exp.get('extracted_skills'):
                print(f"    Extracted Skills: {len(exp['extracted_skills'])} skills found")
        
        # Test normalization statistics
        stats = entity_norm.get_normalization_stats(normalized_skills)
        print(f"\n📊 Normalization Statistics:")
        print(f"  Total: {stats['total']}")
        print(f"  Exact Matches: {stats['exact_matches']}")
        print(f"  Fuzzy Matches: {stats['fuzzy_matches']}")
        print(f"  No Matches: {stats['no_matches']}")
        print(f"  Average Confidence: {stats['average_confidence']:.3f}")
        
        entity_norm.close()
        return True
        
    except Exception as e:
        print(f"❌ Entity Normalization Service Test Failed: {str(e)}")
        return False

def test_candidate_metrics_service():
    """Test the candidate metrics service."""
    print("\n🔍 Testing Candidate Metrics Service...")
    
    try:
        # Initialize metrics service
        metrics_service = CandidateMetricsService()
        
        # Test candidate profile
        test_candidate = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "skills": ["Python", "JavaScript", "React", "AWS", "Docker"],
            "standardized_skills": ["Python", "JavaScript", "React", "Amazon Web Services", "Docker"],
            "work_experience": [
                {
                    "company": "Google Inc.",
                    "title": "Software Engineer",
                    "start_date": "2020-01-01",
                    "end_date": "2023-06-30",
                    "responsibilities": [
                        "Developed Python applications",
                        "Built React frontend components",
                        "Deployed applications using AWS"
                    ]
                },
                {
                    "company": "Startup XYZ",
                    "title": "Junior Developer",
                    "start_date": "2018-03-01",
                    "end_date": "2019-12-31",
                    "responsibilities": [
                        "Developed JavaScript applications",
                        "Worked with Docker containers"
                    ]
                }
            ],
            "education": [
                {
                    "degree": "Bachelor of Science in Computer Science",
                    "institution": "Stanford University",
                    "graduation_year": 2018
                }
            ]
        }
        
        print("\n🧪 Testing Candidate Metrics Calculation:")
        
        # Calculate metrics
        metrics = metrics_service.calculate_candidate_metrics(test_candidate)
        
        # Display results
        print(f"📊 Calculated Metrics:")
        print(f"  Total Experience Years: {metrics['total_experience_years']}")
        print(f"  Relevant Experience Years: {metrics['relevant_experience_years']}")
        print(f"  Average Tenure (months): {metrics['average_tenure_months']}")
        print(f"  Longest Tenure (months): {metrics['longest_tenure_months']}")
        print(f"  Job Stability Score: {metrics['job_stability_score']:.2f}/10")
        print(f"  Universal Profile Score: {metrics['universal_profile_score']:.2f}/10")
        print(f"  Seniority Level: {metrics['seniority_level']}")
        print(f"  Career Progression Score: {metrics['career_progression_score']:.2f}/10")
        print(f"  Company Prestige Score: {metrics['company_prestige_score']:.2f}/10")
        print(f"  Skill Depth Score: {metrics['skill_depth_score']:.2f}/10")
        
        # Display domain-specific experience
        print(f"\n🏢 Domain-Specific Experience:")
        for domain, years in metrics['domain_relevant_experience'].items():
            print(f"  {domain.replace('_', ' ').title()}: {years} years")
        
        # Display tenure distribution
        print(f"\n⏱️ Tenure Distribution:")
        for i, tenure in enumerate(metrics['tenure_distribution']):
            print(f"  Job {i+1}: {tenure} months")
        
        metrics_service.close()
        return True
        
    except Exception as e:
        print(f"❌ Candidate Metrics Service Test Failed: {str(e)}")
        return False

def test_integration():
    """Test the complete integration of all services."""
    print("\n🔍 Testing Complete Integration...")
    
    try:
        # Test a complete candidate processing pipeline
        test_candidate_data = {
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
            "skills": ["python", "react", "aws", "docker", "kubernetes"],
            "work_experience": [
                {
                    "company": "Microsoft",
                    "title": "Senior Software Engineer",
                    "start_date": "2019-01-01",
                    "end_date": "2023-12-31",
                    "responsibilities": [
                        "Led Python development team",
                        "Architected React applications",
                        "Managed AWS infrastructure"
                    ]
                },
                {
                    "company": "Tech Startup",
                    "title": "Software Developer",
                    "start_date": "2017-06-01",
                    "end_date": "2018-12-31",
                    "responsibilities": [
                        "Developed JavaScript applications",
                        "Used Docker for deployment"
                    ]
                }
            ]
        }
        
        print("\n🧪 Testing Complete Pipeline:")
        
        # Step 1: Entity Normalization
        entity_norm = EntityNormalizationService()
        normalized_skills = entity_norm.normalize_skills(test_candidate_data["skills"])
        normalized_work_exp = entity_norm.normalize_work_experience(test_candidate_data["work_experience"])
        
        print("✅ Entity Normalization Complete")
        
        # Step 2: Metrics Calculation
        metrics_service = CandidateMetricsService()
        metrics = metrics_service.calculate_candidate_metrics(test_candidate_data)
        
        print("✅ Metrics Calculation Complete")
        
        # Step 3: Display Results
        print(f"\n📋 Integration Results:")
        print(f"  Candidate: {test_candidate_data['name']}")
        print(f"  Normalized Skills: {len(normalized_skills)} skills processed")
        print(f"  Normalized Work Experience: {len(normalized_work_exp)} positions processed")
        print(f"  Universal Profile Score: {metrics['universal_profile_score']:.2f}/10")
        print(f"  Seniority Level: {metrics['seniority_level']}")
        
        # Show some normalized skills
        print(f"\n🔧 Sample Normalized Skills:")
        for skill_data in normalized_skills[:3]:  # Show first 3
            print(f"  {skill_data['original']} -> {skill_data['canonical']} "
                  f"({skill_data['match_type']}, {skill_data['confidence']:.2f})")
        
        entity_norm.close()
        metrics_service.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Integration Test Failed: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting Neo4j, Entity Normalization, and Candidate Metrics Integration Tests")
    print("=" * 80)
    
    # Check if Neo4j is configured
    print(f"🔧 Configuration Check:")
    print(f"  Neo4j URI: {settings.NEO4J_URI}")
    print(f"  Neo4j User: {settings.NEO4J_USER}")
    print(f"  Neo4j Password: {'*' * len(settings.NEO4J_PASSWORD) if settings.NEO4J_PASSWORD else 'Not set'}")
    
    # Run tests
    tests = [
        ("Ontology Service", test_ontology_service),
        ("Entity Normalization Service", test_entity_normalization_service),
        ("Candidate Metrics Service", test_candidate_metrics_service),
        ("Complete Integration", test_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running {test_name} Test...")
        print(f"{'='*60}")
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name} Test: PASSED")
            else:
                print(f"❌ {test_name} Test: FAILED")
                
        except Exception as e:
            print(f"❌ {test_name} Test: ERROR - {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 TEST SUMMARY")
    print(f"{'='*80}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Neo4j integration is working correctly.")
    else:
        print("⚠️ Some tests failed. Please check the configuration and Neo4j setup.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
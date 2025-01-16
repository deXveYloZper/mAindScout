# app/utils/nlp_utils.py

import spacy
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import fuzz, process
from nltk.stem import WordNetLemmatizer
from typing import List, Dict
import os
import json
import re
from app.utils.classification_data import JOB_CATEGORIES_KEYWORDS, CANDIDATE_CATEGORIES_KEYWORDS

# Load spaCy English model
nlp = spacy.load('en_core_web_sm')

# Make sure to download the necessary NLTK data
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')  # For lemmatization

# Load the skills taxonomy from the JSON file at the module level
taxonomy_path = os.path.join('app', 'data', 'skills_taxonomy.json')
try:
    with open(taxonomy_path, 'r', encoding='utf-8') as f:
        skills_taxonomy = json.load(f)
except FileNotFoundError:
    skills_taxonomy = {}
    print(f"Warning: Skills taxonomy file not found at {taxonomy_path}. Skills will not be standardized.")
except json.JSONDecodeError as e:
    skills_taxonomy = {}
    print(f"Error decoding skills taxonomy JSON: {str(e)}. Skills will not be standardized.")


def extract_keywords(text: str, num_keywords: int = 15) -> List[str]:
    """
    Extract relevant keywords from a text using TF-IDF scoring with lemmatization and n-grams.

    Args:
    - text (str): The input text to extract keywords from.
    - num_keywords (int): The number of top keywords to return.

    Returns:
    - List[str]: The top keywords extracted from the text.
    """
    # Preprocess the text
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    words = nltk.word_tokenize(text)

    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    words_filtered = [word for word in words if word not in stop_words]

    # Lemmatization
    lemmatizer = WordNetLemmatizer()
    words_lemmatized = [lemmatizer.lemmatize(word) for word in words_filtered]

    # Join back into a single string for TF-IDF processing
    processed_text = ' '.join(words_lemmatized)

    # Use TF-IDF to extract unigrams and bigrams
    vectorizer = TfidfVectorizer(max_features=num_keywords, ngram_range=(1, 2))
    vectors = vectorizer.fit_transform([processed_text])
    feature_names = vectorizer.get_feature_names_out()

    # Get the highest scoring keywords
    keywords = sorted(
        zip(feature_names, vectors.toarray()[0]),
        key=lambda x: x[1],
        reverse=True
    )

    # Return only the words, not the scores
    return [keyword for keyword, score in keywords]

def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extract entities from the text using spaCy's NER with improved filtering.

    Args:
    - text (str): The text to extract entities from.

    Returns:
    - Dict[str, List[str]]: A dictionary of entities by type.
    """
    doc = nlp(text)
    entities = {}
    for ent in doc.ents:
        # Improved filtering: Include part-of-speech checks for relevance
        if ent.label_ in ['ORG', 'GPE', 'PRODUCT', 'EVENT'] and len(ent.text) > 3:
            # Ensure the entity contains proper nouns or nouns
            if any(token.pos_ in ['NOUN', 'PROPN'] for token in ent):
                label = ent.label_
                entities.setdefault(label, set()).add(ent.text)

    # Convert sets to lists before returning
    return {label: list(texts) for label, texts in entities.items()}



def classify_job(text: str) -> List[str]:
    """
    Classify the job description into categories based on keywords.
    """
    categories = []
    text_lower = text.lower()
    for category, keywords in JOB_CATEGORIES_KEYWORDS.items():
        for keyword in keywords:
            # Use word boundaries to match whole words
            pattern = rf'\b{re.escape(keyword.lower())}\b'
            if re.search(pattern, text_lower):
                categories.append(category)
                break  # Avoid duplicate categories if multiple keywords match
    return categories

def classify_candidate(text: str) -> List[str]:
    """
    Classify the candidate's expertise areas based on the resume.
    """
    categories = []
    text_lower = text.lower()
    for category, keywords in CANDIDATE_CATEGORIES_KEYWORDS.items():
        for keyword in keywords:
            pattern = rf'\b{re.escape(keyword.lower())}\b'
            if re.search(pattern, text_lower):
                categories.append(category)
                break  # Avoid duplicate categories if multiple keywords match
    return categories


# Load the skills taxonomy from a JSON file at the module level
taxonomy_path = os.path.join('app', 'data', 'skills_taxonomy.json')
with open(taxonomy_path, 'r') as f:
    taxonomy = json.load(f)


def standardize_skills(skills: List[str]) -> List[str]:
    """
    Standardize skill names to a consistent format using the skills taxonomy.

    Args:
    - skills (List[str]): A list of raw skill names.

    Returns:
    - List[str]: A list of standardized skill names.
    """
    # Predefined mapping for common abbreviations and aliases
    predefined_skill_mapping = {
        "aws": "Amazon Web Services",
        "gcp": "Google Cloud Platform",
        "nlp": "Natural Language Processing",
        # Add more mappings if necessary
    }

    # Initialize lemmatizer
    lemmatizer = WordNetLemmatizer()
    standardized_skills = set()

    for skill in skills:
        skill_lower = skill.lower().strip()

        # Step 1: Check in predefined mapping
        if skill_lower in predefined_skill_mapping:
            standardized_skills.add(predefined_skill_mapping[skill_lower])
            continue

        # Step 2: Exact match in skills taxonomy
        if skill_lower in skills_taxonomy:
            standardized_skills.add(skills_taxonomy[skill_lower])
            continue

        # Step 3: Lemmatize the skill and search in taxonomy
        skill_lemma = lemmatizer.lemmatize(skill_lower)
        if skill_lemma in skills_taxonomy:
            standardized_skills.add(skills_taxonomy[skill_lemma])
            continue

        # Step 4: Fuzzy match with rapidfuzz if no exact match found
        best_match, match_score, index = process.extractOne(skill_lemma, skills_taxonomy.keys(), scorer=fuzz.token_sort_ratio)
        if match_score > 80:  # Adjustable threshold based on testing
            standardized_skills.add(skills_taxonomy[best_match])
        else:
            # Step 5: Fallback to title case for consistency
            standardized_skills.add(skill.title())

    return list(standardized_skills)

def flatten_taxonomy(nested_taxonomy, parent_key='', sep=' > '):
    """
    Flatten a nested taxonomy dictionary.

    Args:
        nested_taxonomy (dict): The nested taxonomy.
        parent_key (str): The base key to use for nested keys.
        sep (str): Separator between parent and child keys.

    Returns:
        dict: A flat dictionary with tags as keys and lists of keywords as values.
    """
    flat_taxonomy = {}
    for key, value in nested_taxonomy.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            # Recursively flatten the dictionary
            flat_taxonomy.update(flatten_taxonomy(value, new_key, sep=sep))
        elif isinstance(value, list):
            # Assign the list of keywords to the new key
            flat_taxonomy[new_key] = value
        else:
            # Handle unexpected types
            flat_taxonomy[new_key] = [value]
    return flat_taxonomy

def generate_company_tags(description: str, flat_taxonomy: Dict[str, List[str]]) -> List[str]:
    """
    Generate relevant tags for a company based on its description using TF-IDF scoring.

    Args:
    - description (str): The company description.
    - flat_taxonomy (Dict[str, List[str]]): A flattened taxonomy of keywords.

    Returns:
    - List[str]: A list of relevant tags.
    """
    tag_scores = {}
    for tag, keywords in flat_taxonomy.items():
        # Use TF-IDF to score keywords
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([description, ' '.join(keywords)])
        
        # Calculate cosine similarity between description and keywords
        tag_score = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]  

        if tag_score > 0:
            tag_scores[tag] = tag_score

    # Set a relevance threshold and limit to max tags
    relevance_threshold = 0.1  # Adjust based on testing
    filtered_tags = [tag for tag, score in tag_scores.items() if score >= relevance_threshold]

    # Sort tags by their scores in descending order
    sorted_tags = sorted(filtered_tags, key=lambda tag: tag_scores[tag], reverse=True)

    # Limit the number of tags to a maximum of 10
    max_tags = 10
    return sorted_tags[:max_tags]
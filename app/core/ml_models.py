from sentence_transformers import SentenceTransformer
import spacy

class ModelManager:
    embedding_model: SentenceTransformer = None
    nlp_model: spacy.language.Language = None

model_manager = ModelManager()

def load_models():
    # This heavy loading happens only once at startup
    model_manager.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    model_manager.nlp_model = spacy.load('en_core_web_sm')

def get_embedding_model():
    return model_manager.embedding_model

def get_nlp_model():
    return model_manager.nlp_model 
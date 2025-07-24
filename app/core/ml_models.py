from sentence_transformers import SentenceTransformer
import spacy

class ModelManager:
    def __init__(self):
        # These heavy models are now loaded only once at startup
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.nlp_model = spacy.load('en_core_web_sm')

model_manager = ModelManager()

def get_embedding_model() -> SentenceTransformer:
    return model_manager.embedding_model

def get_nlp_model() -> spacy.language.Language:
    return model_manager.nlp_model 
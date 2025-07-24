# app/services/tagging_service.py

import logging
from typing import List, Dict
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.multioutput import MultiOutputClassifier
from sklearn.linear_model import LogisticRegression
import joblib


class TaggingService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.vectorizer = None
        self.model = None
        self.mlb = None

    def load_data(self, data_path: str) -> pd.DataFrame:
        """
        Load and preprocess the data from the specified path.
        """
        df = pd.read_csv(data_path)
        df = df[['id', 'company_description', 'tags']].dropna()
        df['tags'] = df['tags'].apply(lambda x: x.split(','))
        return df

    def train_model(self, df: pd.DataFrame):
        """
        Train the multi-label classification model.
        """
        # Preprocess text data
        descriptions = df['company_description'].values
        self.vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
        X = self.vectorizer.fit_transform(descriptions)

        # Encode tags
        self.mlb = MultiLabelBinarizer()
        y = self.mlb.fit_transform(df['tags'])

        # Train model
        classifier = LogisticRegression(max_iter=1000)
        self.model = MultiOutputClassifier(classifier, n_jobs=-1)
        self.model.fit(X, y)

        self.logger.info("Model training completed.")

    def save_model(self, model_path: str):
        """
        Save the trained model and vectorizer to disk.
        """
        joblib.dump({
            'vectorizer': self.vectorizer,
            'model': self.model,
            'mlb': self.mlb
        }, model_path)
        self.logger.info(f"Model saved to {model_path}.")

    def load_model(self, model_path: str):
        """
        Load the trained model and vectorizer from disk.
        """
        data = joblib.load(model_path)
        self.vectorizer = data['vectorizer']
        self.model = data['model']
        self.mlb = data['mlb']
        self.logger.info("Model loaded successfully.")

    def predict_tags(self, descriptions: List[str]) -> List[List[str]]:
        """
        Predict tags for the given company descriptions.
        """
        X = self.vectorizer.transform(descriptions)
        y_pred = self.model.predict(X)
        tags = self.mlb.inverse_transform(y_pred)
        return tags

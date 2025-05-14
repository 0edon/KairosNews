import spacy
from typing import List, Union
import logging

logger = logging.getLogger(__name__)

class NLPModel:
    def __init__(self):
        try:
            # Load spaCy model only
            self.nlp = spacy.load("pt_core_news_md")
            logger.info("spaCy model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize spaCy model: {str(e)}")
            raise

    def extract_entities(self, text: Union[str, List[str]]) -> List[tuple]:
        """Entity extraction using spaCy"""
        try:
            if isinstance(text, list):
                text = " ".join(text)
            doc = self.nlp(text)
            return [(ent.text.lower(), ent.label_) for ent in doc.ents]
        except Exception as e:
            logger.error(f"Entity extraction failed: {str(e)}")
            return []

    def tokenize_sentences(self, text: str) -> List[str]:
        """Sentence tokenization using spaCy"""
        try:
            doc = self.nlp(text)
            return [sent.text for sent in doc.sents]
        except Exception as e:
            logger.error(f"Sentence tokenization failed: {str(e)}")
            return [text]  # Fallback to returning whole text
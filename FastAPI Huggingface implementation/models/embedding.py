from sentence_transformers import SentenceTransformer
import torch

class EmbeddingModel:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    
    def encode(self, text: str):
        return self.model.encode(text, device=self.device)
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class EmbeddingEngine:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def similarity(self, text_a: str, text_b: str) -> float:
        emb = self.model.encode([text_a, text_b])
        return cosine_similarity([emb[0]], [emb[1]])[0][0]

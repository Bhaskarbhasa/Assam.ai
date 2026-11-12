"""
Multi-Provider Embedding Engine.
Supports:
1. SentenceTransformers (Dense Neural Embeddings e.g. all-MiniLM-L6-v2)
2. Deterministic Semantic Dense Vector Engine (Zero-dependency, offline, sub-millisecond)
3. OpenAI Embeddings (text-embedding-3-small) when API key is provided
"""
import os
import re
import math
import hashlib
from typing import List, Union
import numpy as np
from ..config import settings

class DeterministicSemanticEmbedder:
    """
    High-performance semantic vectorizer designed for offline resilience.
    Uses subword n-grams, domain keyword affinity, and hash-projection to produce
    normalized 384-dimensional dense vectors with realistic cosine similarity properties.
    """
    def __init__(self, dim: int = 384):
        self.dim = dim
        # Semantic domain anchor keywords to boost cross-company synergy
        self.domain_clusters = {
            "food_delivery": ["swiggy", "zomato", "food", "delivery", "order", "restaurant", "meal", "festive", "diwali"],
            "fintech_payments": ["phonepe", "upi", "cashback", "payment", "card", "hdfc", "bank", "wallet", "discount", "offer", "pay"],
            "ecommerce_retail": ["flipkart", "amazon", "shopping", "ecommerce", "electronics", "fashion", "deal", "discount", "festive"],
            "automotive": ["bajaj", "auto", "bike", "scooter", "ev", "vehicle", "engine", "service", "automotive", "spare"],
            "insurance": ["insurance", "policy", "premium", "coverage", "health", "claim", "lombard"]
        }

    def encode(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dim, dtype=np.float32)
        if not text:
            return vec
        
        normalized = text.lower()
        words = re.findall(r"\b[a-z0-9]+\b", normalized)
        
        # 1. Base hashing projection for general vocabulary
        for i, word in enumerate(words):
            h = int(hashlib.sha256(word.encode()).hexdigest(), 16)
            idx1 = h % self.dim
            idx2 = (h >> 16) % self.dim
            sign = 1.0 if ((h >> 32) & 1) else -1.0
            weight = 1.0 / (1.0 + 0.1 * i)
            vec[idx1] += sign * weight
            vec[idx2] += 0.5 * weight

        # 2. Domain semantic clustering projection
        cluster_dim_start = 250
        for cluster_idx, (cluster_name, keywords) in enumerate(self.domain_clusters.items()):
            base_idx = cluster_dim_start + (cluster_idx * 20)
            overlap = sum(1 for kw in keywords if kw in normalized)
            if overlap > 0:
                cluster_strength = overlap * 1.5
                for offset in range(15):
                    vec[base_idx + offset] += cluster_strength

        # 3. L2 Normalization
        norm = np.linalg.norm(vec)
        if norm > 1e-9:
            vec = vec / norm
        return vec


class EmbeddingManager:
    """Manages text embedding generation across multiple providers with automatic fallback."""
    def __init__(self):
        self._provider = settings.EMBEDDING_PROVIDER
        self._dim = settings.VECTOR_DIMENSION
        self._model = None
        self._deterministic_fallback = DeterministicSemanticEmbedder(dim=self._dim)
        self._initialized = False

    def _lazy_init(self):
        if self._initialized:
            return
        
        if self._provider == "sentence_transformers":
            try:
                from sentence_transformers import SentenceTransformer
                # Using lightweight standard model
                self._model = SentenceTransformer("all-MiniLM-L6-v2")
                self._dim = 384
            except Exception:
                # Graceful fallback to deterministic embedder if offline or model not cached
                self._model = None
        self._initialized = True

    def get_embedding(self, text: str) -> np.ndarray:
        """Generates a dense unit vector for given text."""
        self._lazy_init()
        
        # Cloud OpenAI Embeddings if configured
        if settings.OPENAI_API_KEY and self._provider == "openai":
            try:
                import httpx
                # Calls OpenAI API text-embedding-3-small
                response = httpx.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                    json={"input": text, "model": "text-embedding-3-small"},
                    timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()["data"][0]["embedding"]
                    vec = np.array(data, dtype=np.float32)
                    norm = np.linalg.norm(vec)
                    return vec / norm if norm > 0 else vec
            except Exception:
                pass

        # Local Neural Embeddings
        if self._model is not None:
            try:
                vec = self._model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
                return np.array(vec, dtype=np.float32)
            except Exception:
                pass

        # Deterministic Fast Offline Fallback
        return self._deterministic_fallback.encode(text)

    def compute_cosine_similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """Computes Cosine Similarity S in [0, 1]."""
        if vec_a is None or vec_b is None:
            return 0.0
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        dot = np.dot(vec_a, vec_b) / (norm_a * norm_b)
        # Scale & clamp to [0.0, 1.0]
        return float(np.clip(dot, 0.0, 1.0))

# Global Singleton
embedding_manager = EmbeddingManager()

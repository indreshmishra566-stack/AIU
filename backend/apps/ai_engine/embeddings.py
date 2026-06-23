"""
AIU — Embedding Service
Lightweight deterministic embeddings with no external ML dependency.
"""

import hashlib
import struct

from django.conf import settings
from django.core.cache import cache

EMBED_CACHE_TTL = 86400 * 7
DIMENSION = settings.AI_ENGINE.get("EMBEDDING_DIMENSION", 384)


class EmbeddingService:
    """Deterministic local embeddings for semantic-ish ranking without extra downloads."""

    def embed(self, text: str) -> list[float]:
        text = text.strip()
        if not text:
            return [0.0] * DIMENSION

        cache_key = f"aiu:emb:{hashlib.md5(text.encode()).hexdigest()}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        vector = self._hash_embed(text)
        cache.set(cache_key, vector, timeout=EMBED_CACHE_TTL)
        return vector

    def _hash_embed(self, text: str) -> list[float]:
        """Deterministic hash-based embedding that keeps cosine ranking stable enough for fallback use."""
        h = hashlib.sha256(text.encode()).digest()
        raw = (h * ((DIMENSION * 4 // len(h)) + 1))[:DIMENSION * 4]
        floats = list(struct.unpack(f"{DIMENSION}f", raw))
        magnitude = sum(x * x for x in floats) ** 0.5 or 1.0
        return [x / magnitude for x in floats]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts if t.strip()]

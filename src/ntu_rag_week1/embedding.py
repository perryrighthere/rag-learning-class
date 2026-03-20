from __future__ import annotations

import hashlib
import math
import re


STOPWORDS = {
    "的",
    "了",
    "是",
    "在",
    "和",
    "就",
    "都",
    "要",
    "不",
    "让",
    "与",
    "及",
    "先",
    "再",
    "很",
    "更",
    "一个",
    "我们",
}


def tokenize(text: str) -> list[str]:
    lowered = text.lower()
    ascii_tokens = re.findall(r"[a-z0-9_]+", lowered)
    cjk_tokens = [char for char in lowered if "\u4e00" <= char <= "\u9fff"]
    tokens = ascii_tokens + cjk_tokens
    return [token for token in tokens if token not in STOPWORDS and token.strip()]


class HashingEmbedder:
    def __init__(self, dimension: int = 128) -> None:
        if dimension < 16:
            raise ValueError("dimension must be >= 16")
        self.dimension = dimension

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        for token in tokenize(text):
            digest = hashlib.md5(token.encode("utf-8")).hexdigest()
            index = int(digest, 16) % self.dimension
            vector[index] += 1.0
        return _normalize(vector)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]

"""BM25 sparse-вектор для гибридного поиска.

Простая реализация BM25 для построения sparse-векторов.
Каждый токен → индекс в словаре, значение → BM25 вес.

Поддерживает инкрементальное добавление документов через add_documents().
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass


@dataclass
class SparseVector:
    """Разреженный вектор: индексы + значения."""

    indices: list[int]
    values: list[float]


class BM25Encoder:
    """Энкодер BM25 sparse-векторов для Qdrant.

    Инкрементальный: add_documents() добавляет документы к существующему корпусу.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self._k1 = k1
        self._b = b
        self._vocab: dict[str, int] = {}
        self._doc_freq: Counter[str] = Counter()
        self._doc_count: int = 0
        self._total_len: int = 0

    def fit(self, documents: list[str]) -> None:
        """Построить словарь и IDF с нуля по корпусу документов.

        Сбрасывает предыдущее состояние. Для инкрементального добавления
        используй add_documents().
        """
        self._vocab = {}
        self._doc_freq = Counter()
        self._doc_count = 0
        self._total_len = 0
        self.add_documents(documents)

    def add_documents(self, documents: list[str]) -> None:
        """Добавить документы к существующему корпусу (инкрементально)."""
        for doc in documents:
            tokens = self._tokenize(doc)
            self._total_len += len(tokens)
            self._doc_count += 1
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self._doc_freq[token] += 1
                if token not in self._vocab:
                    self._vocab[token] = len(self._vocab)

    @property
    def avg_doc_len(self) -> float:
        return self._total_len / max(self._doc_count, 1)

    def encode(self, text: str) -> SparseVector:
        """Вычислить BM25 sparse-вектор для текста документа."""
        tokens = self._tokenize(text)
        if not tokens:
            return SparseVector(indices=[], values=[])

        tf = Counter(tokens)
        doc_len = len(tokens)

        indices: list[int] = []
        values: list[float] = []

        for token, count in tf.items():
            idx = self._vocab.get(token)
            if idx is None:
                continue

            # IDF: log((N - df + 0.5) / (df + 0.5) + 1)
            df = self._doc_freq.get(token, 0)
            idf = math.log((self._doc_count - df + 0.5) / (df + 0.5) + 1.0)

            # BM25 TF: (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl/avgdl))
            tf_norm = (count * (self._k1 + 1)) / (
                count + self._k1 * (1 - self._b + self._b * doc_len / max(self.avg_doc_len, 1))
            )

            score = idf * tf_norm
            if score > 0:
                indices.append(idx)
                values.append(score)

        return SparseVector(indices=indices, values=values)

    def encode_query(self, query: str) -> SparseVector:
        """Вычислить sparse-вектор для поискового запроса.

        Для запросов используем IDF без нормализации длины.
        """
        tokens = self._tokenize(query)
        if not tokens:
            return SparseVector(indices=[], values=[])

        tf = Counter(tokens)
        indices: list[int] = []
        values: list[float] = []

        for token, count in tf.items():
            idx = self._vocab.get(token)
            if idx is None:
                continue

            df = self._doc_freq.get(token, 0)
            idf = math.log((self._doc_count - df + 0.5) / (df + 0.5) + 1.0)

            if idf > 0:
                indices.append(idx)
                values.append(idf * count)

        return SparseVector(indices=indices, values=values)

    @property
    def vocab_size(self) -> int:
        return len(self._vocab)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Токенизация: нижний регистр, буквы/цифры от 2 символов. Кириллица + латиница."""
        text = text.lower()
        return re.findall(r"[a-zа-яё0-9]{2,}", text)

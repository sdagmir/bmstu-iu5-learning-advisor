"""Фейки внешних зависимостей (OpenRouter, embeddings) для integration-тестов."""

from __future__ import annotations

from typing import Any


class FakeLLMClient:
    """Фейк OpenRouterClient. Возвращает заранее запрограммированные ответы.

    По умолчанию отвечает простым текстом. Через `queue_response` можно положить
    в очередь ответ с tool_calls — для тестов function calling.
    """

    def __init__(self, model: str = "fake/test-model") -> None:
        self._model = model
        self.calls: list[dict[str, Any]] = []
        self._queue: list[dict[str, Any]] = []

    @property
    def model(self) -> str:
        return self._model

    @model.setter
    def model(self, value: str) -> None:
        self._model = value

    def queue_response(self, response: dict[str, Any]) -> None:
        """Добавить ответ в очередь — он будет возвращён следующим вызовом chat()."""
        self._queue.append(response)

    def queue_text(self, content: str) -> None:
        """Положить текстовый ответ в очередь."""
        self.queue_response(
            {"choices": [{"message": {"role": "assistant", "content": content}}]}
        )

    def queue_tool_call(
        self,
        function_name: str,
        arguments_json: str = "{}",
        tool_call_id: str = "call_test",
    ) -> None:
        """Положить ответ с одним tool_call в очередь."""
        self.queue_response(
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": tool_call_id,
                                    "type": "function",
                                    "function": {
                                        "name": function_name,
                                        "arguments": arguments_json,
                                    },
                                }
                            ],
                        }
                    }
                ]
            }
        )

    async def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        self.calls.append({"messages": messages, "tools": tools})
        if self._queue:
            return self._queue.pop(0)
        # Дефолт — пустой текстовый ответ
        return {"choices": [{"message": {"role": "assistant", "content": "ok"}}]}

    async def close(self) -> None:
        pass


class FakeEmbeddingClient:
    """Фейк EmbeddingClient. Возвращает детерминированные псевдо-эмбеддинги по hash-у текста."""

    def __init__(self, dimension: int = 1536) -> None:
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def _vector(self, text: str) -> list[float]:
        # Простая детерминированная функция: hash → нормализованный вектор
        h = abs(hash(text))
        return [((h >> (i % 32)) & 0xFF) / 255.0 for i in range(self._dimension)]

    async def embed(self, text: str) -> list[float]:
        return self._vector(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]

    async def close(self) -> None:
        pass

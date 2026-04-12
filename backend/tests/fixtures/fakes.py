"""Fake implementations for testing."""

from app.modules.evaluacion_docente.domain.schemas.query import GeminiCallResult


class FakeFileStorage:
    """In-memory file storage for testing — no real I/O."""

    def __init__(self) -> None:
        self.files: dict[str, tuple[bytes, str]] = {}

    async def upload(self, path: str, data: bytes, content_type: str) -> str:
        self.files[path] = (data, content_type)
        return path

    async def download(self, path: str) -> bytes:
        if path not in self.files:
            raise FileNotFoundError(f"File not found: {path}")
        return self.files[path][0]

    async def delete(self, path: str) -> None:
        self.files.pop(path, None)


class FakeGeminiGateway:
    """In-memory Gemini gateway that returns canned responses."""

    def __init__(
        self,
        *,
        answer: str = "Respuesta de prueba basada en la evidencia [1].",
        model_name: str = "gemini-2.0-flash",
        tokens_input: int = 100,
        tokens_output: int = 50,
        latency_ms: int = 200,
        error: Exception | None = None,
    ) -> None:
        self.answer = answer
        self.model_name = model_name
        self.tokens_input = tokens_input
        self.tokens_output = tokens_output
        self.latency_ms = latency_ms
        self.error = error
        self.calls: list[dict] = []

    async def answer_query(
        self,
        question: str,
        comments: list[dict],
        metrics: list[dict],
    ) -> GeminiCallResult:
        self.calls.append(
            {
                "question": question,
                "comments": comments,
                "metrics": metrics,
            }
        )
        if self.error:
            raise self.error
        return GeminiCallResult(
            text=self.answer,
            model_name=self.model_name,
            tokens_input=self.tokens_input,
            tokens_output=self.tokens_output,
            latency_ms=self.latency_ms,
        )

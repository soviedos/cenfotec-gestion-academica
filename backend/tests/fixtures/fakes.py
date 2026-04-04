"""Fake implementations for testing."""


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

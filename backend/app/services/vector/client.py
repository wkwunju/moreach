from typing import Protocol


class VectorStore(Protocol):
    def upsert(self, vectors: list[dict]) -> None:
        ...

    def query(self, vector: list[float], top_k: int) -> list[dict]:
        ...

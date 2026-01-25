from typing import Protocol


class GoogleSearchProvider(Protocol):
    def search(self, query: str, limit: int) -> list[dict]:
        ...


class InstagramScrapeProvider(Protocol):
    def profile(self, handle: str) -> dict:
        ...

    def recent_posts(self, handle: str, limit: int) -> list[dict]:
        ...

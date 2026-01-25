from __future__ import annotations

from abc import ABC, abstractmethod

from typing import List, Dict, Optional, Any


class TopicRepoError(Exception):
    pass


class TopicRepository(ABC):
    """Abstract interface for topic storage backends.

    Concrete implementations may store topics on the filesystem, in sqlite,
    or other backends.
    """

    @abstractmethod
    def list_topics(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_topic(self, id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def create_topic(self, title: str, body: str) -> Any:
        pass

    @abstractmethod
    def delete_topic(self, id: str) -> bool:
        pass

    @abstractmethod
    def random_topic_id(self) -> Optional[Any]:
        pass

    @abstractmethod
    def search(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        pass


__all__ = ["TopicRepository", "FileTopicRepository", "TopicRepoError"]

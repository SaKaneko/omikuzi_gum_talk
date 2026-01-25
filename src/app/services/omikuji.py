import random
from typing import Optional
from ..repositories.topic_repo_sqlite import SQLiteTopicRepository


class OmikujiService:
    def __init__(self, repo: Optional[SQLiteTopicRepository] = None):
        self.repo = repo or SQLiteTopicRepository()

    def pick_random_topic(self) -> Optional[str]:
        rid = self.repo.random_topic_id()
        return str(rid) if rid is not None else None

import random
from typing import Optional

from ..repositories.topic_repo import TopicRepository


class OmikujiService:
    def __init__(self, repo: Optional[TopicRepository] = None):
        self.repo = repo or TopicRepository()

    def pick_random_topic(self) -> Optional[str]:
        topics = self.repo.list_topics()
        if not topics:
            return None
        return random.choice(topics)["id"]

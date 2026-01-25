import os
import re
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

from .topic_repo import TopicRepository, TopicRepoError


class FileTopicRepository(TopicRepository):
    """Filesystem-backed topic repository (original implementation).

    Kept for backwards compatibility and as a concrete TopicRepository.
    """

    def __init__(self, topics_dir: Optional[str] = None):
        if topics_dir:
            self.topics_dir = Path(topics_dir)
        else:
            # default to project-root/topics
            self.topics_dir = Path(__file__).resolve().parents[3] / "topics"
        self.topics_dir.mkdir(parents=True, exist_ok=True)

    def _safe_id(self, filename: str) -> str:
        return Path(filename).stem

    def list_topics(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        out = []
        files = sorted(self.topics_dir.glob("*.md"))
        if limit:
            files = files[:limit]
        for p in files:
            try:
                with p.open("r", encoding="utf-8") as f:
                    first = f.readline().strip()
            except Exception:
                first = ""
            out.append({"id": self._safe_id(p.name), "title": first})
        return out

    def get_topic(self, id: str) -> Dict[str, Any]:
        if not re.match(r"^[A-Za-z0-9_\-]+$", id):
            raise TopicRepoError("invalid id")
        path = self._path_for_id(id)
        if not path.exists():
            raise TopicRepoError("not found")
        with path.open("r", encoding="utf-8") as f:
            lines = f.readlines()
        title = lines[0].strip() if lines else ""
        body = "".join(lines[1:]).lstrip("\n") if len(lines) > 1 else ""
        return {"id": id, "title": title, "body": body}

    def create_topic(self, title: str, body: str) -> str:
        if not title or not body:
            raise TopicRepoError("title and body required")
        # safe slug
        slug = (
            re.sub(r"[^A-Za-z0-9\-]+", "-", title.strip())[:50].strip("-").lower()
            or "topic"
        )
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{ts}_{slug}.md"
        dest = self.topics_dir / filename

        tmp = None
        try:
            fd, tmp_path = tempfile.mkstemp(
                prefix="topic_", suffix=".tmp", dir=str(self.topics_dir)
            )
            tmp = Path(tmp_path)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(title.strip() + "\n")
                f.write(body.strip() + "\n")
            # atomic replace
            os.replace(str(tmp), str(dest))
            return self._safe_id(dest.name)
        except Exception as e:
            if tmp and tmp.exists():
                try:
                    tmp.unlink()
                except Exception:
                    pass
            raise TopicRepoError(str(e))

    def delete_topic(self, id: str) -> bool:
        path = self._path_for_id(id)
        if not path.exists():
            raise TopicRepoError("not found")
        try:
            path.unlink()
            return True
        except Exception as e:
            raise TopicRepoError(str(e))

    def _path_for_id(self, id: str) -> Path:
        # find matching file by stem
        for p in self.topics_dir.glob("*.md"):
            if p.stem == id:
                return p
        return self.topics_dir / (id + ".md")

    def random_topic_id(self) -> Optional[str]:
        files = list(self.topics_dir.glob("*.md"))
        if not files:
            return None
        import random

        p = random.choice(files)
        return self._safe_id(p.name)

    def search(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        out = []
        q = query.lower()
        for p in sorted(self.topics_dir.glob("*.md")):
            with p.open("r", encoding="utf-8") as f:
                lines = f.read()
            if q in lines.lower():
                out.append(
                    {
                        "id": self._safe_id(p.name),
                        "title": lines.splitlines()[0] if lines else "",
                    }
                )
            if len(out) >= limit:
                break
        return out


__all__ = ["TopicRepository", "FileTopicRepository", "TopicRepoError"]

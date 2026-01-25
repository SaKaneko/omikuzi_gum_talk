import os
import re
import sqlite3
import time
import unicodedata
from typing import Optional, List, Dict, Any

from .topic_repo import TopicRepository, TopicRepoError


def _slugify(text: str) -> str:
    # Simple slugify: normalize, replace non-alnum with '-', trim
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = text.strip().lower()
    # replace spaces and slashes
    text = re.sub(r"[\s/]+", "-", text)
    # remove characters except alnum, hyphen, underscore
    text = re.sub(r"[^\w\-]+", "", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


class SQLiteTopicRepository(TopicRepository):
    """SQLite-backed implementation of `TopicRepository`."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.environ.get("TOPICS_DB", "data/topics.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        # enable WAL for concurrency
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def ensure_schema(self) -> None:
        schema_path = os.path.join(os.path.dirname(__file__), "schema_sqlite.sql")
        if not os.path.exists(schema_path):
            raise FileNotFoundError(f"schema file not found: {schema_path}")
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        conn = self._get_conn()
        try:
            conn.executescript(schema_sql)
            conn.commit()
        finally:
            conn.close()

    def list_topics(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        q = "SELECT id, slug, title, created_at FROM topics ORDER BY created_at DESC"
        if limit:
            q += f" LIMIT {int(limit)}"
        conn = self._get_conn()
        try:
            cur = conn.execute(q)
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def get_topic(self, topic_id: int) -> Optional[Dict[str, Any]]:
        conn = self._get_conn()
        try:
            cur = conn.execute(
                "SELECT id, slug, title, body, created_at, updated_at FROM topics WHERE id = ?",
                (topic_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def _unique_slug(self, base: str) -> str:
        slug = base or str(int(time.time()))
        if not slug:
            slug = str(int(time.time()))
        conn = self._get_conn()
        try:
            cur = conn.execute("SELECT 1 FROM topics WHERE slug = ? LIMIT 1", (slug,))
            if not cur.fetchone():
                return slug
            # append numeric suffix until unique
            i = 1
            while True:
                candidate = f"{slug}-{i}"
                cur = conn.execute(
                    "SELECT 1 FROM topics WHERE slug = ? LIMIT 1", (candidate,)
                )
                if not cur.fetchone():
                    return candidate
                i += 1
        finally:
            conn.close()

    def create_topic(
        self,
        title: str,
        body: str,
        slug: Optional[str] = None,
    ) -> int:
        if not title or not body:
            raise ValueError("title and body are required")
        base = _slugify(slug or title)
        if not base:
            base = str(int(time.time()))
        slug_final = self._unique_slug(base)
        conn = self._get_conn()
        try:
            cur = conn.execute(
                "INSERT INTO topics (slug, title, body) VALUES (?, ?, ?)",
                (slug_final, title, body),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def delete_topic(self, id):
        return self.hard_delete(id)

    def soft_delete(self, topic_id: int) -> bool:
        conn = self._get_conn()
        try:
            conn.execute(
                "",
                (topic_id,),
            )
            conn.commit()
        except Exception:
            return False
        finally:
            conn.close()
        return True

    def hard_delete(self, topic_id: int) -> bool:
        conn = self._get_conn()
        try:
            conn.execute(
                "DELETE FROM topics WHERE id = ?",
                (topic_id,),
            )
            conn.commit()
        except Exception:
            return False
        finally:
            conn.close()
        return True

    def random_topic_id(self) -> Optional[int]:
        conn = self._get_conn()
        try:
            cur = conn.execute("SELECT id FROM topics ORDER BY RANDOM() LIMIT 1")
            row = cur.fetchone()
            return int(row["id"]) if row else None
        finally:
            conn.close()

    def search(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        try:
            # prefer FTS if available
            try:
                cur = conn.execute(
                    "SELECT topics.id, topics.title FROM topics JOIN topics_fts ON topics_fts.rowid = topics.id WHERE topics_fts MATCH ? LIMIT ?",
                    (query, limit),
                )
                return [dict(r) for r in cur.fetchall()]
            except sqlite3.OperationalError:
                # fallback to LIKE search
                q = "%" + query.replace("%", "\%") + "%"
                cur = conn.execute(
                    "SELECT id, title FROM topics WHERE (title LIKE ? OR body LIKE ?) LIMIT ?",
                    (q, q, limit),
                )
                return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()


# Backwards-compatible exports: many modules import TopicRepository from this module.
TopicRepository = SQLiteTopicRepository
__all__ = ["SQLiteTopicRepository", "TopicRepository", "TopicRepoError"]

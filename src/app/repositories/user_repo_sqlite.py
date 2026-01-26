from __future__ import annotations

import sqlite3
from typing import Optional, Dict
from datetime import datetime

from app.utils.password_manager import PasswordManager
from app.repositories.user_repo import UserRepository


class SQLiteUserRepository(UserRepository):
    """SQLite-backed implementation of `UserRepository`.

    Uses the `users` table and `PasswordManager` for hashing and verification.
    """

    def __init__(self, db_path: str, password_manager: PasswordManager):
        self.db_path = db_path
        self.pwm = password_manager
        self._ensure_table()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table(self) -> None:
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT NOT NULL UNIQUE,
              password_hash TEXT NOT NULL,
              salt TEXT NOT NULL,
              created_at DATETIME NOT NULL DEFAULT (datetime('now')),
              updated_at DATETIME,
              roles TEXT NOT NULL DEFAULT ''
            );
            """
        )
        conn.commit()
        conn.close()

    def create_user(
        self, username: str, password: str, roles: list | None = None
    ) -> int:
        """Create a new user. Returns the inserted user id."""
        salt = self.pwm.generate_salt()
        password_hash = self.pwm.hash_password(password, salt)
        conn = self._get_conn()
        cur = conn.cursor()
        try:
            roles = roles or ["user"]
            roles_str = ",".join(roles)
            cur.execute(
                "INSERT INTO users (username, password_hash, salt, created_at, roles) VALUES (?, ?, ?, ?, ?)",
                (
                    username,
                    password_hash,
                    salt,
                    datetime.utcnow().isoformat(),
                    roles_str,
                ),
            )
            conn.commit()
            user_id = cur.lastrowid
        finally:
            conn.close()
        return user_id

    def get_user(self, username: str) -> Optional[Dict]:
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        d = dict(row)
        # normalize roles column into a list
        raw = d.get("roles") or ""
        d["roles"] = [r for r in (raw.split(",") if raw else []) if r]
        return d

    def verify_user(self, username: str, password: str) -> bool:
        user = self.get_user(username)
        if not user:
            return False
        return self.pwm.verify_password(password, user["salt"], user["password_hash"])

    def change_password(
        self, username: str, old_password: str, new_password: str
    ) -> bool:
        user = self.get_user(username)
        if not user:
            return False
        try:
            new_salt, new_hash = self.pwm.change_password(
                old_password, new_password, user["salt"], user["password_hash"]
            )
        except ValueError:
            return False
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET salt = ?, password_hash = ? WHERE username = ?",
            (new_salt, new_hash, username),
        )
        conn.commit()
        conn.close()
        return True

    def delete_user(self, username: str) -> bool:
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE username = ?", (username,))
        changed = cur.rowcount
        conn.commit()
        conn.close()
        return bool(changed)


__all__ = ["SQLiteUserRepository"]

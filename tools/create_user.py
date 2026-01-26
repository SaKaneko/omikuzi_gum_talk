#!/usr/bin/env python3
"""
Development helper: create a user in the application's users DB.

Usage:
  PYTHONPATH=src python3 tools/create_user.py username password [--db data/users.db] [--roles admin,user]

If `--roles` omitted, the user will get the default role `user`.
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from src.app.utils.password_manager import PasswordManager


def ensure_db(db_path: str) -> None:
    """Ensure the DB exists and is initialized using the project's SQL schema file.

    Falls back to creating a minimal `users` table if the schema file can't be found.
    """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        # locate schema file relative to repo root
        project_root = Path(__file__).resolve().parents[1]
        schema_path = (
            project_root / "src" / "app" / "repositories" / "schema_sqlite.sql"
        )
        if schema_path.exists():
            sql = schema_path.read_text(encoding="utf-8")
            conn.executescript(sql)
            conn.commit()
        else:
            return
    finally:
        conn.close()
    return


def create_user(
    db_path: str, username: str, password: str, roles: list[str] | None = None
) -> int:
    """Create a user in the specified users DB. Returns the inserted user id."""
    pwm = PasswordManager()
    salt = pwm.generate_salt()
    password_hash = pwm.hash_password(password, salt)
    conn = sqlite3.connect(db_path)
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
        return cur.lastrowid
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a user in the dev users DB")
    parser.add_argument("username")
    parser.add_argument("password")
    parser.add_argument("--db", default="data/data.db", help="Path to users DB")
    parser.add_argument(
        "--roles", default="admin", help="Comma-separated roles (e.g. admin,user)"
    )
    args = parser.parse_args()

    db_path = args.db
    ensure_db(db_path)
    roles = [r for r in args.roles.split(",") if r] if args.roles else ["user"]
    try:
        uid = create_user(db_path, args.username, args.password, roles)
        print(f"created user id: {uid}")
    except sqlite3.IntegrityError as e:
        print("Error: could not create user:", e)
        sys.exit(2)

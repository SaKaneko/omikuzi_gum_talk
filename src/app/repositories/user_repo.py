from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Dict


class UserRepository(ABC):
    """Abstract interface for user management.

    Concrete implementations may store users in memory, sqlite, or other backends.
    """

    @abstractmethod
    def create_user(self, username: str, password: str) -> int:
        """Create a user and return its id."""

    @abstractmethod
    def get_user(self, username: str) -> Optional[Dict]:
        """Return user record as a dict or None if not found."""

    @abstractmethod
    def verify_user(self, username: str, password: str) -> bool:
        """Return True if the supplied password matches the stored credentials."""

    @abstractmethod
    def change_password(
        self, username: str, old_password: str, new_password: str
    ) -> bool:
        """Change a user's password. Return True on success."""

    @abstractmethod
    def delete_user(self, username: str) -> bool:
        """Delete a user. Return True if a row was deleted."""


__all__ = ["UserRepository"]

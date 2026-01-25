("""
PasswordManager

Provides secure password hashing, verification and rotation utilities.

Uses PBKDF2-HMAC-SHA256 with a per-user random salt.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Tuple


class PasswordManager:
	def __init__(self, iterations: int = 200_000, dklen: int = 32, salt_bytes: int = 16):
		self.iterations = iterations
		self.dklen = dklen
		self.salt_bytes = salt_bytes

	def generate_salt(self, length: int | None = None) -> str:
		"""Generate a random salt and return it as a hex string."""
		length = length or self.salt_bytes
		return secrets.token_bytes(length).hex()

	def hash_password(self, password: str, salt_hex: str) -> str:
		"""Return hex-encoded PBKDF2-HMAC-SHA256 derived key for given password+salt."""
		dk = hashlib.pbkdf2_hmac(
			"sha256",
			password.encode("utf-8"),
			bytes.fromhex(salt_hex),
			self.iterations,
			dklen=self.dklen,
		)
		return dk.hex()

	def verify_password(self, password: str, salt_hex: str, expected_hash_hex: str) -> bool:
		"""Verify that `password` with `salt_hex` produces `expected_hash_hex`.

		Comparison is done with constant-time `hmac.compare_digest`.
		"""
		computed = self.hash_password(password, salt_hex)
		return hmac.compare_digest(computed, expected_hash_hex)

	def change_password(self, old_password: str, new_password: str, salt_hex: str, stored_hash_hex: str) -> Tuple[str, str]:
		"""If `old_password` matches the stored hash, generate a new salt and return (new_salt_hex, new_hash_hex).

		Raises ValueError if verification fails.
		"""
		if not self.verify_password(old_password, salt_hex, stored_hash_hex):
			raise ValueError("old password does not match")
		new_salt = self.generate_salt()
		new_hash = self.hash_password(new_password, new_salt)
		return new_salt, new_hash


__all__ = ["PasswordManager"]


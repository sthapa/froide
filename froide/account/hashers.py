"""
From: https://docs.djangoproject.com/en/1.11/topics/auth/passwords/#password-upgrading-without-requiring-a-login
"""

from django.contrib.auth.hashers import (
    PBKDF2PasswordHasher,
    SHA1PasswordHasher,
)


class PBKDF2WrappedSHA1PasswordHasher(PBKDF2PasswordHasher):
    algorithm = "pbkdf2_wrapped_sha1"

    def encode_sha1_hash(self, sha1_hash, salt, iterations=None):
        return super(PBKDF2WrappedSHA1PasswordHasher, self).encode(
            sha1_hash, salt, iterations
        )

    def encode(self, password, salt, iterations=None):
        _, _, sha1_hash = SHA1PasswordHasher().encode(password, salt).split("$", 2)
        return self.encode_sha1_hash(sha1_hash, salt, iterations)

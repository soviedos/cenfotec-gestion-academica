"""Authentication service — Google OAuth token exchange and session management.

Responsibilities:
    - Initiate OAuth flow (build authorization URL)
    - Exchange authorization code for access/id tokens
    - Validate Google ID token and extract user info
    - Create or update local user record on first login
    - Issue/revoke application session tokens
"""

from __future__ import annotations


class AuthService:
    """Orchestrates Google OAuth 2.0 login flow and session lifecycle."""

    # TODO: implement with google-auth / httpx
    pass

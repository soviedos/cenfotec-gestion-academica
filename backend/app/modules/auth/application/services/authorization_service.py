"""Authorization service — role-based access control (RBAC).

Responsibilities:
    - Verify that the current user has the required role for an action
    - Provide FastAPI dependencies for route-level authorization guards
    - Map Google Workspace groups/claims to application roles
"""

from __future__ import annotations


class AuthorizationService:
    """Checks permissions for the authenticated user."""

    # TODO: implement role checks
    pass

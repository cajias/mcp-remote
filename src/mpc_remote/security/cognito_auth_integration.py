"""Cognito Authentication Integration Module."""

from typing import Any, Dict, Optional

from .cognito_authenticator import CognitoAuthenticator


class CognitoAuthIntegration:
    """
    Integration layer for Cognito authentication in the MPC Remote system.

    Provides methods for authentication, token validation, and user management.
    """

    def __init__(self, authenticator: Optional[CognitoAuthenticator] = None) -> None:
        """
        Initialize the Cognito authentication integration.

        :param authenticator: Optional custom CognitoAuthenticator instance
        """
        self.authenticator = authenticator or CognitoAuthenticator()

    def authenticate(self, username: str, password: str) -> Dict[str, str]:
        """
        Authenticate a user and retrieve tokens.

        :param username: User's username
        :param password: User's password
        :return: Authentication tokens
        """
        return self.authenticator.initiate_auth(username, password)

    def validate_token(self, token: str, user_record: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate a JWT token and optionally check against a user record.

        :param token: JWT token to validate
        :param user_record: Optional user record for additional validation
        :return: Decoded token claims
        :raises ValueError: If token is invalid
        """
        claims = self.authenticator.verify_token(token)

        # Optional additional validation against user record
        if user_record and claims.get("sub") != user_record.get("id"):
            raise ValueError("Token does not match the user record")

        return claims

    def refresh_tokens(self, refresh_token: str) -> Dict[str, str]:
        """
        Refresh authentication tokens.

        :param refresh_token: Current refresh token
        :return: New access and ID tokens
        """
        return self.authenticator.refresh_tokens(refresh_token)


def cognito_auth_handler(
    *, username: str, password: Optional[str] = None, token: Optional[str] = None, user_record: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Legacy authentication handler compatible with the previous implementation.

    :param username: Username (can be used for extra checks)
    :param password: Ignored for Cognito
    :param token: The Cognito JWT token
    :param user_record: The stored user record for the user
    :return: The user_record, augmented with token claims
    :raises ValueError: if token is missing or invalid.
    """
    auth_integration = CognitoAuthIntegration()

    if token is None:
        raise ValueError("Cognito authentication requires a token")

    claims = auth_integration.validate_token(token, user_record)

    # Augment the user record with the claims
    user_record["claims"] = claims
    return user_record

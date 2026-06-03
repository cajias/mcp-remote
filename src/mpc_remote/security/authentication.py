"""Authentication mechanisms for Model Context Protocol"""

from typing import Any, Callable, Dict, Optional


class AuthenticationManager:
    """
    Manages authentication for Model Context Protocol

    Provides flexible authentication mechanisms by allowing
    custom authentication callbacks to be registered with string keys.
    """

    def __init__(self) -> None:
        """Initialize authentication manager"""
        self._users: Dict[str, Dict[str, Any]] = {}
        self._auth_methods: Dict[str, Callable[..., Dict[str, Any]]] = {}

    def register_user(
        self, username: str, password: Optional[str] = None, auth_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Register a new user

        :param username: Unique username
        :param password: User password
        :param auth_data: Additional authentication data
        :return: Generated user ID
        """
        if username in self._users:
            raise ValueError(f"User {username} already exists")

        # Generate salt and hash password
        import hashlib
        import hmac
        import secrets

        salt = secrets.token_hex(16)
        hashed_password = (
            hmac.new(salt.encode("utf-8"), password.encode("utf-8"), hashlib.sha256).hexdigest() if password else None
        )

        user_id = secrets.token_urlsafe(16)
        user_record = {
            "id": user_id,
            "username": username,
            "salt": salt,
            "password_hash": hashed_password,
            "auth_data": auth_data or {},
            "active": True,
        }
        self._users[username] = user_record
        return user_id

    def authenticate(
        self, username: str, password: Optional[str] = None, token: Optional[str] = None, method: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Authenticate a user using the specified method.

        If a custom method is registered under `method`, it will be used.
        Otherwise, default authentication is applied.
        """
        if username not in self._users:
            raise ValueError("User not found")
        user = self._users[username]
        if not user.get("active", False):
            raise ValueError("User account is not active")

        # Use a custom method if provided
        if method:
            if method in self._auth_methods:
                return self._auth_methods[method](username=username, password=password, token=token, user_record=user)
            else:
                raise ValueError(f"No authentication method registered for '{method}'")
        # Default: no authentication (or you can implement a default flow here)
        return user

    def add_custom_auth_method(self, method_name: str, handler: Callable[..., Dict[str, Any]]) -> None:
        """
        Register a custom authentication method.

        :param method_name: A string identifier for the method (e.g. "cognito")
        :param handler: A callback that takes username, password, token, and user_record,
                        and returns an authenticated user context.
        """
        self._auth_methods[method_name] = handler

    def generate_token(self, username: str, expiry: Optional[int] = None) -> str:
        """
        Generate an authentication token

        :param username: Username
        :param expiry: Token expiration time (seconds)
        :return: Generated token
        """
        if username not in self._users:
            raise ValueError("User not found")
        import secrets
        import time

        token = secrets.token_urlsafe(32)
        user = self._users[username]
        user["token"] = token
        if expiry:
            user["token_expiry"] = time.time() + expiry
        return token

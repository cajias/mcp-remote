"""Authentication mechanisms for Model Context Protocol"""

import hashlib
import hmac
import secrets
from enum import Enum, auto
from typing import Any, Callable, Dict, Optional


class AuthenticationMethod(Enum):
    """Supported authentication methods"""
    NONE = auto()
    TOKEN = auto()
    JWT = auto()
    HMAC = auto()

class AuthenticationManager:
    """
    Manages authentication for Model Context Protocol
    
    Provides flexible authentication mechanisms
    """
    def __init__(self):
        """Initialize authentication manager"""
        self._users: Dict[str, Dict[str, Any]] = {}
        self._auth_methods: Dict[str, Callable] = {}
    
    def register_user(
        self, 
        username: str, 
        password: Optional[str] = None,
        auth_data: Optional[Dict[str, Any]] = None
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
        salt = secrets.token_hex(16)
        hashed_password = self._hash_password(password, salt) if password else None
        
        # Create user record
        user_id = secrets.token_urlsafe(16)
        user_record = {
            'id': user_id,
            'username': username,
            'salt': salt,
            'password_hash': hashed_password,
            'auth_data': auth_data or {},
            'active': True
        }
        
        self._users[username] = user_record
        return user_id
    
    def _hash_password(self, password: str, salt: str) -> str:
        """
        Hash password using HMAC-SHA256
        
        :param password: Plain text password
        :param salt: Password salt
        :return: Hashed password
        """
        return hmac.new(
            salt.encode('utf-8'), 
            password.encode('utf-8'), 
            hashlib.sha256
        ).hexdigest()
    
    def authenticate(
        self, 
        username: str, 
        password: Optional[str] = None,
        token: Optional[str] = None,
        method: AuthenticationMethod = AuthenticationMethod.NONE
    ) -> Dict[str, Any]:
        """
        Authenticate a user
        
        :param username: Username
        :param password: User password
        :param token: Authentication token
        :param method: Authentication method
        :return: User authentication context
        """
        if username not in self._users:
            raise ValueError("User not found")
        
        user = self._users[username]
        
        # Check user is active
        if not user.get('active', False):
            raise ValueError("User account is not active")
        
        # Custom method authentication
        if method in self._auth_methods:
            return self._auth_methods[method](
                username=username, 
                password=password, 
                token=token, 
                user_record=user
            )
        
        # Default authentication methods
        if method == AuthenticationMethod.NONE:
            return user
        
        if method == AuthenticationMethod.TOKEN:
            # Validate token
            if not token or token != user.get('token'):
                raise ValueError("Invalid authentication token")
            return user
        
        if method == AuthenticationMethod.PASSWORD:
            # Password authentication
            if not password:
                raise ValueError("Password required")
            
            # Hash and compare password
            hashed_input = self._hash_password(password, user['salt'])
            if not hmac.compare_digest(hashed_input, user['password_hash']):
                raise ValueError("Invalid password")
            
            return user
        
        raise ValueError(f"Unsupported authentication method: {method}")
    
    def add_custom_auth_method(
        self, 
        method: AuthenticationMethod, 
        handler: Callable
    ):
        """
        Add a custom authentication method
        
        :param method: Authentication method
        :param handler: Authentication handler function
        """
        self._auth_methods[method] = handler
    
    def generate_token(
        self, 
        username: str, 
        expiry: Optional[int] = None
    ) -> str:
        """
        Generate an authentication token
        
        :param username: Username
        :param expiry: Token expiration time (seconds)
        :return: Generated token
        """
        if username not in self._users:
            raise ValueError("User not found")
        
        # Generate secure token
        token = secrets.token_urlsafe(32)
        
        # Update user record
        user = self._users[username]
        user['token'] = token
        if expiry:
            user['token_expiry'] = time.time() + expiry
        
        return token

# Example usage
def example_authentication():
    """Demonstrate authentication functionality"""
    auth_manager = AuthenticationManager()
    
    # Register a user
    user_id = auth_manager.register_user(
        username='example_user', 
        password='secure_password'
    )
    
    # Authenticate user
    try:
        user_context = auth_manager.authenticate(
            username='example_user', 
            password='secure_password',
            method=AuthenticationMethod.PASSWORD
        )
        print("Authentication successful")
        
        # Generate token
        token = auth_manager.generate_token('example_user')
        print(f"Generated token: {token}")
    except ValueError as e:
        print(f"Authentication failed: {e}")

# Main execution
if __name__ == "__main__":
    example_authentication()

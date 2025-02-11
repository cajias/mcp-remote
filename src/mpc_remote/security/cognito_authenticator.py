"""Cognito Authentication Module."""
import json
import os
import time
import urllib.request
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import boto3
from jwt.algorithms import RSAAlgorithm


def _validate_https_url(url: str) -> str:
    """
    Validate and return URL only if it uses HTTPS scheme.

    :param url: URL to validate
    :return: Original URL if it uses HTTPS
    :raises ValueError: If URL scheme is not HTTPS
    """
    parsed_url = urlparse(url)
    if parsed_url.scheme != 'https':
        raise ValueError(f"Only HTTPS URLs are allowed. Got: {url}")
    return url


class CognitoAuthenticator:
    """
    Advanced Cognito authentication handler with robust token management.

    Key Features:
    - Configurable via environment variables
    - Automatic public key caching
    - Token verification
    - Token refresh support
    - Comprehensive error handling
    """

    def __init__(
        self,
        pool_id: Optional[str] = None,
        region: Optional[str] = None,
        client_id: Optional[str] = None
    )->None:
        """
        Initialize Cognito Authenticator with configurable parameters.

        :param pool_id: Cognito User Pool ID (optional, reads from env)
        :param region: AWS Region (optional, reads from env)
        :param client_id: Cognito Client ID (optional, reads from env)
        """
        # Prioritize passed parameters, then environment variables
        self.pool_id = pool_id or os.getenv('COGNITO_POOL_ID')
        self.region = region or os.getenv('AWS_REGION')
        self.client_id = client_id or os.getenv('COGNITO_CLIENT_ID')

        if not all([self.pool_id, self.region, self.client_id]):
            raise ValueError(
                "Missing Cognito configuration. "
                "Set COGNITO_POOL_ID, AWS_REGION, and COGNITO_CLIENT_ID environment variables."
            )

        # Construct JWK URL with HTTPS validation
        self.jwks_url = _validate_https_url(
            f"https://cognito-idp.{self.region}.amazonaws.com/{self.pool_id}/.well-known/jwks.json"
        )

        # Initialize public keys cache
        self._public_keys: Optional[Dict[str, Any]] = None
        self._keys_last_fetched = 0

        # Initialize Cognito Identity Provider client
        self.cognito_client = (
            boto3.client('cognito-idp', region_name=self.region)
            if boto3 is not None
            else None
        )

    def _fetch_public_keys(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Fetch Cognito public keys, with caching to reduce unnecessary network calls.

        :param force_refresh: Force fetching new keys
        :return: Dictionary of public keys
        """
        # Cache keys for 1 hour to reduce network calls
        current_time = time.time()
        if (not force_refresh and
            self._public_keys is not None and
            (current_time - self._keys_last_fetched) < 3600):
            return self._public_keys

        try:
            url = _validate_https_url(self.jwks_url)
            with urllib.request.urlopen(url) as response:  # noqa: S310
                jwks = json.load(response)

            self._public_keys = {
                key["kid"]: RSAAlgorithm.from_jwk(json.dumps(key))
                for key in jwks["keys"]
            }

            self._keys_last_fetched = current_time

            return self._public_keys

        except Exception as e:
            raise RuntimeError(f"Failed to fetch Cognito public keys: {e}") from e

# Cognito Authentication for MPC Remote

## Prerequisites

1. AWS Account with Amazon Cognito configured
2. User Pool created
3. App Client generated

## Environment Configuration
    
Set the following environment variables:

```bash
export COGNITO_POOL_ID='your-cognito-user-pool-id'
export AWS_REGION='your-aws-region'
export COGNITO_CLIENT_ID='your-cognito-app-client-id'
```

### AWS Credentials

Ensure AWS credentials are configured. You can do this in several ways:
- AWS CLI configuration: `aws configure`
- Environment variables:
  ```bash
  export AWS_ACCESS_KEY_ID='your-access-key'
  export AWS_SECRET_ACCESS_KEY='your-secret-key'
  ```
- AWS Credentials file (`~/.aws/credentials`)

## Key Features

- Token verification
- Token refresh
- Secure authentication flow
- Comprehensive error handling

## Example Usage

```python
from mpc_remote.security.cognito_auth_integration import CognitoAuthIntegration

# Initialize authenticator
auth_integration = CognitoAuthIntegration()

# Authenticate user
tokens = auth_integration.authenticate('username', 'password')

# Validate token
claims = auth_integration.validate_token(tokens['access_token'])

# Refresh tokens
new_tokens = auth_integration.refresh_tokens(tokens['refresh_token'])
```

## Security Considerations

- Never store tokens in plain text
- Use secure storage mechanisms
- Implement proper token rotation
- Monitor and log authentication attempts

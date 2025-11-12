# Authentication Setup Guide

This project uses **django-allauth** for authentication. Currently, password-based authentication is configured, but you can easily add social authentication providers.

## Current Setup: Password-Based Authentication

The system is configured to use email and password for authentication:

- **Authentication Method**: Email + Password
- **Email Verification**: Optional (can be made mandatory)
- **Username**: Not required (email is used as identifier)

### User Registration Flow

1. User provides email and password
2. Optional email verification (if enabled)
3. User can log in with email and password

## Adding Social Authentication Providers

Django-allauth supports many OAuth providers. Here's how to add the most common ones:

### Prerequisites

For all providers, you need to:

1. Register your application with the OAuth provider
2. Obtain Client ID and Client Secret
3. Configure callback URLs
4. Add the provider to Django settings
5. Create a Social Application in Django Admin

### Adding Google Login

#### 1. Register Your App with Google

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth 2.0 Client ID"
5. Configure consent screen if prompted
6. Application type: Web application
7. Add authorized redirect URIs:
   - `http://localhost:8000/accounts/google/login/callback/` (development)
   - `https://your-domain.com/accounts/google/login/callback/` (production)
8. Note your Client ID and Client Secret

#### 2. Install Google Provider

Add to `settings/base.py`:

```python
INSTALLED_APPS = [
    # ... existing apps ...
    "allauth.socialaccount.providers.google",
]
```

#### 3. Configure in Django Admin

1. Run migrations: `python manage.py migrate`
2. Access Django admin: `/admin/`
3. Go to "Sites" and ensure your domain is correctly set
4. Go to "Social applications" > "Add social application"
   - Provider: Google
   - Name: Google OAuth
   - Client ID: (from step 1)
   - Secret key: (from step 1)
   - Sites: Select your site
5. Save

#### 4. Add Login Button to Frontend

```html
<a href="{% provider_login_url 'google' %}">Login with Google</a>
```

### Adding Microsoft Login

#### 1. Register Your App with Microsoft

1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to "Azure Active Directory" > "App registrations"
3. Click "New registration"
4. Name your application
5. Supported account types: Choose based on your needs
6. Redirect URI: Web, `https://your-domain.com/accounts/microsoft/login/callback/`
7. Register and note your Application (client) ID
8. Go to "Certificates & secrets" > "New client secret"
9. Note the secret value (shown only once!)

#### 2. Install Microsoft Provider

Add to `settings/base.py`:

```python
INSTALLED_APPS = [
    # ... existing apps ...
    "allauth.socialaccount.providers.microsoft",
]
```

#### 3. Configure in Django Admin

Same as Google, but:
- Provider: Microsoft
- Client ID: Application (client) ID from Azure
- Secret key: Client secret value from Azure

### Adding GitHub Login

#### 1. Register Your App with GitHub

1. Go to [GitHub Settings](https://github.com/settings/developers)
2. Click "New OAuth App"
3. Application name: Your app name
4. Homepage URL: `https://your-domain.com`
5. Authorization callback URL: `https://your-domain.com/accounts/github/login/callback/`
6. Register application
7. Note your Client ID and generate a Client Secret

#### 2. Install GitHub Provider

Add to `settings/base.py`:

```python
INSTALLED_APPS = [
    # ... existing apps ...
    "allauth.socialaccount.providers.github",
]
```

#### 3. Configure in Django Admin

Same process as above with GitHub credentials.

### Adding Slack Login

#### 1. Create Slack App

1. Go to [Slack API](https://api.slack.com/apps)
2. Click "Create New App"
3. Choose "From scratch"
4. Name your app and choose workspace
5. Navigate to "OAuth & Permissions"
6. Add Redirect URL: `https://your-domain.com/accounts/slack/login/callback/`
7. Add OAuth scopes:
   - `identity.basic`
   - `identity.email`
8. Note your Client ID and Client Secret from "Basic Information"

#### 2. Install Slack Provider

Add to `settings/base.py`:

```python
INSTALLED_APPS = [
    # ... existing apps ...
    "allauth.socialaccount.providers.slack",
]
```

#### 3. Configure in Django Admin

Same process with Slack credentials.

## Environment Variables

For production, it's recommended to store credentials as environment variables:

```bash
# .env file
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

MICROSOFT_CLIENT_ID=your_microsoft_client_id
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret

GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

SLACK_CLIENT_ID=your_slack_client_id
SLACK_CLIENT_SECRET=your_slack_client_secret
```

Then configure dynamically in settings (advanced):

```python
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': config('GOOGLE_CLIENT_ID'),
            'secret': config('GOOGLE_CLIENT_SECRET'),
            'key': ''
        }
    },
    # ... similar for other providers
}
```

## Additional Configuration Options

### Email Verification

To make email verification mandatory:

```python
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
```

### Require Email for Social Accounts

```python
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_EMAIL_VERIFICATION = "optional"
```

### Auto-Connect Social Accounts

Allow users to connect social accounts automatically if email matches:

```python
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_REQUIRED = True
```

### Customize Social Account Data

You can request additional data from providers:

```python
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}
```

## Testing Authentication Locally

1. Ensure you have configured callback URLs for `localhost:8000` or `127.0.0.1:8000`
2. Use ngrok or similar tools if providers don't support localhost
3. Test the full OAuth flow
4. Check that user data is correctly saved

## Security Best Practices

1. **Never commit secrets to Git**: Use environment variables
2. **Use HTTPS in production**: OAuth providers require HTTPS
3. **Validate redirect URIs**: Ensure only your domains are whitelisted
4. **Regular key rotation**: Rotate client secrets periodically
5. **Minimal scopes**: Only request the OAuth scopes you actually need
6. **Session security**: Use secure session cookies in production

## Troubleshooting

### "Redirect URI mismatch" Error

- Check that the callback URL in provider settings exactly matches your configuration
- Include/exclude trailing slashes consistently
- Check HTTP vs HTTPS
- For development, ensure `localhost` vs `127.0.0.1` matches

### "Invalid Client" Error

- Verify Client ID and Secret are correct
- Check that the provider app is enabled/active
- Ensure credentials haven't expired

### Email Already Exists

- This happens when a user tries to sign up with a social provider using an email already registered
- Configure `SOCIALACCOUNT_AUTO_SIGNUP = False` to let users connect accounts manually

## Frontend Integration

For React frontend, you can redirect users to allauth URLs:

```typescript
// Login with Google
window.location.href = '/accounts/google/login/';

// Login with GitHub
window.location.href = '/accounts/github/login/';
```

Or create API endpoints that return OAuth URLs for better UX.

## Support

For more providers and advanced configuration, see:
- [django-allauth documentation](https://django-allauth.readthedocs.io/)
- [Supported providers list](https://django-allauth.readthedocs.io/en/latest/providers.html)


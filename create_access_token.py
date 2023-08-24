import requests

# Your Azure AD tenant ID
tenant_id = '<>'

# Your app's client ID and secret
client_id = '<>'
client_secret = '<>'

# The OAuth2 token endpoint
token_url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'

# The data for the token request
token_data = {
    'grant_type': 'client_credentials',
    'client_id': client_id,
    'client_secret': client_secret,
    'scope': 'https://graph.microsoft.com/.default'
}

# Send the token request
response = requests.post(token_url, data=token_data)

# Get the access token from the response
access_token = response.json().get('access_token')

print(access_token)

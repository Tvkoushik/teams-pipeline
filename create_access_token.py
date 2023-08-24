import requests

# Your Azure AD tenant ID
tenant_id = 'de4d316d-888b-4234-ae27-31c8fd9e1c03'

# Your app's client ID and secret
client_id = 'a292e31b-1db8-4b4e-9420-c854b7dea9cd'
client_secret = 'fo28Q~IvhCwvK.GjwOonXsMc1c4.8TZSPROAGdxz'

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

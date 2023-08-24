import requests
import json

# Your access token from Azure AD
access_token = '<>'

# The headers for the request
headers = {
    'Authorization': 'Bearer ' + access_token,
    'Content-Type': 'application/json'
}

# The endpoint URL
url = 'https://graph.microsoft.com/v1.0/subscriptions'

# The subscription details
subscription_data = {
    "changeType": "created",
    "notificationUrl": "<>",
    "resource": "/communications/callRecords",
    "expirationDateTime": "2023-08-02T00:00:00.0000000Z",  # Use a valid date within the next 3 days
    "clientState": "sample"  # Use a secret value known to your application
}

# Send the request
response = requests.post(url, headers=headers, data=json.dumps(subscription_data))

# Print the response
print(response.json())

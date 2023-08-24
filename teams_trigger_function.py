import logging
import json
import requests
import pandas as pd
#import pyodbc

def get_access_token(client_id: str, client_secret: str, tenant_id: str) -> str:
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'client_id': client_id,
        'scope': 'https://graph.microsoft.com/.default',
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    response = requests.post(url, headers=headers, data=data)
    return response.json()['access_token']

# Parse the request body JSON
data = json.loads("""{
  "value": [
    {
      "subscriptionId": "a8cea9ce-70ac-4166-b2d3-9463bd25c971",
      "clientState": "sample",
      "changeType": "created",
      "resource": "communications/callRecords/6211a1bb-c8c4-4c0e-8688-d5e0ebf86c5e",
      "subscriptionExpirationDateTime": "2023-07-29T00:00:00+00:00",
      "resourceData": {
        "@odata.type": "#Microsoft.Graph.callrecord",
        "@odata.id": "communications/callRecords/6211a1bb-c8c4-4c0e-8688-d5e0ebf86c5e",
        "oDataType": "#microsoft.graph.callrecord",
        "oDataId": "communications/callRecords/6211a1bb-c8c4-4c0e-8688-d5e0ebf86c5e",
        "id": "6211a1bb-c8c4-4c0e-8688-d5e0ebf86c5e"
      },
      "tenantId": "de4d316d-888b-4234-ae27-31c8fd9e1c03"
    }
  ]
}""")
                  

def flatten_call_record(call_record):
    """
    This function specifically flattens the call_record JSON
    """
    # Flatten the organizer and participants
    flattened_call_record = []
    for participant in call_record['participants']:
        record = {}

        # Basic call_record fields
        record['id'] = call_record['id']
        record['version'] = call_record['version']
        record['type'] = call_record['type']
        record['modalities'] = ','.join(call_record['modalities'])
        record['lastModifiedDateTime'] = call_record['lastModifiedDateTime']
        record['startDateTime'] = call_record['startDateTime']
        record['endDateTime'] = call_record['endDateTime']
        record['joinWebUrl'] = call_record['joinWebUrl']

        # Organizer fields
        organizer = call_record['organizer']
        for key in organizer:
            if key in ['user', 'phone']:
                if organizer[key] is not None:
                    for subkey in organizer[key]:
                        record['organizer_' + key + '_' + subkey] = organizer[key][subkey]
            else:
                record['organizer_' + key] = organizer[key]

        # Participant fields
        for key in participant:
            if key in ['user', 'phone']:
                if participant[key] is not None:
                    for subkey in participant[key]:
                        record['participant_' + key + '_' + subkey] = participant[key][subkey]
            else:
                record['participant_' + key] = participant[key]

        flattened_call_record.append(record)

    return flattened_call_record

def flatten_call_sessions(call_sessions):
    """
    This function specifically flattens the call_sessions JSON
    """
    flattened_call_sessions = []

    for call_session in call_sessions:
        flattened_call_session = {}

        # Basic call_session fields
        flattened_call_session['id'] = call_session['id']
        flattened_call_session['modalities'] = ','.join(call_session['modalities'])
        flattened_call_session['startDateTime'] = call_session['startDateTime']
        flattened_call_session['endDateTime'] = call_session['endDateTime']
        flattened_call_session['isTest'] = call_session['isTest']
        flattened_call_session['failureInfo'] = call_session['failureInfo']

        # Caller and Callee fields
        for entity in ['caller', 'callee']:
            for key in call_session[entity]:
                if isinstance(call_session[entity][key], dict):
                    for subkey in call_session[entity][key]:
                        if isinstance(call_session[entity][key][subkey], dict):
                            for super_subkey in call_session[entity][key][subkey]:
                                flattened_call_session[entity + '_' + key + '_' + subkey + '_' + super_subkey] = call_session[entity][key][subkey][super_subkey]
                        else:
                            flattened_call_session[entity + '_' + key + '_' + subkey] = call_session[entity][key][subkey]
                else:
                    flattened_call_session[entity + '_' + key] = call_session[entity][key]

        flattened_call_sessions.append(flattened_call_session)

    return flattened_call_sessions

# Retrieve the call record ID
call_record_id = data['value'][0]['resourceData']['id']

# Fetch the call record details
access_token = get_access_token('<>', '<>', '<>')
headers = {'Authorization': 'Bearer ' + access_token}
response = requests.get('https://graph.microsoft.com/v1.0/communications/callRecords/' + call_record_id, headers=headers)
call_record = response.json()

# Fetch the call session details
response = requests.get('https://graph.microsoft.com/v1.0/communications/callRecords/' + call_record_id + '/sessions', headers=headers)
sessions = response.json()['value']


call_record_flat = flatten_call_record(call_record)
call_session_flat = flatten_call_sessions(sessions)

server="cctestdb.database.windows.net,1433"
database="teams-data-db"
driver="{ODBC Driver 18 for SQL Server}"
query="SELECT count(*) FROM dbo.users"
username = 'ccadmin' 
password = 'fOOLS098&!'

connection_string = 'DRIVER='+driver+';SERVER='+server+';DATABASE='+database+';Uid='+username+';Pwd='+password+';Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
#conn = pyodbc.connect(connection_string)

# cursor = conn.cursor()
# cursor.execute(query) 
# row = cursor.fetchone()
# print(row)

# Create DataFrame and write to SQL
df_record = pd.DataFrame(call_record_flat)
#df_record.to_sql('call_record', conn, if_exists='append', index=False)

df_session = pd.DataFrame(call_session_flat)
#df_session.to_sql('call_session', conn, if_exists='append', index=False)

print(json.dumps(sessions))

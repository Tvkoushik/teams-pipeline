import json
import requests
import azure.functions as func
import pyodbc
import pandas as pd


def get_access_token(client_id: str, client_secret: str, tenant_id: str) -> str:
    """
    Get the access token using client credentials.

    Args:
        client_id (str): The client ID.
        client_secret (str): The client secret.
        tenant_id (str): The Azure AD tenant ID.

    Returns:
        str: The access token.
    """
    try:
        print("Fetching Access Tokens")
        url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "client_id": client_id,
            "scope": "https://graph.microsoft.com/.default",
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        }
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()  # Check for any HTTP errors
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        # Handle any network-related errors
        raise Exception(f"Error while fetching access token: {e}")


def flatten_call_record(call_record):
    """
    Flatten the call_record JSON.

    Args:
        call_record (dict): The call_record JSON.

    Returns:
        list: List of flattened call records as dictionaries.
    """
    print("Flattening Call Records")
    flattened_call_record = []

    try:
        for participant in call_record.get("participants", []):
            record = {}

            # Basic call_record fields
            record["id"] = call_record.get("id")
            record["version"] = call_record.get("version")
            record["type"] = call_record.get("type")
            record["modalities"] = ",".join(call_record.get("modalities", []))
            record["lastModifiedDateTime"] = call_record.get("lastModifiedDateTime")
            record["startDateTime"] = call_record.get("startDateTime")
            record["endDateTime"] = call_record.get("endDateTime")
            record["joinWebUrl"] = call_record.get("joinWebUrl")

            # Organizer fields
            organizer = call_record.get("organizer", {})
            for key in organizer:
                if key in ["user", "phone"]:
                    if organizer[key] is not None:
                        for subkey in organizer[key]:
                            record[f"organizer_{key}_{subkey}"] = organizer[key].get(subkey)
                else:
                    record[f"organizer_{key}"] = organizer.get(key)

            # Participant fields
            for key in participant:
                if key in ["user", "phone"]:
                    if participant[key] is not None:
                        for subkey in participant[key]:
                            record[f"participant_{key}_{subkey}"] = participant[key].get(subkey)
                else:
                    record[f"participant_{key}"] = participant.get(key)

            flattened_call_record.append(record)

        return flattened_call_record

    except KeyError as e:
        # Handle any missing keys in the JSON
        raise Exception(f"Error while flattening call records: Missing key {e}")


def flatten_call_sessions(call_sessions):
    """
    Flatten the call_sessions JSON.

    Args:
        call_sessions (list): List of call_session dictionaries.

    Returns:
        list: List of flattened call sessions as dictionaries.
    """
    print("Flattening Call Sessions")
    flattened_call_sessions = []

    try:
        for call_session in call_sessions:
            flattened_call_session = {}

            # Basic call_session fields
            flattened_call_session["id"] = call_session.get("id")
            flattened_call_session["modalities"] = ",".join(call_session.get("modalities", []))
            flattened_call_session["startDateTime"] = call_session.get("startDateTime")
            flattened_call_session["endDateTime"] = call_session.get("endDateTime")
            flattened_call_session["isTest"] = call_session.get("isTest")
            flattened_call_session["failureInfo"] = call_session.get("failureInfo")

            # Caller and Callee fields
            for entity in ["caller", "callee"]:
                for key in call_session.get(entity, {}):
                    if isinstance(call_session.get(entity, {}).get(key, {}), dict):
                        for subkey in call_session.get(entity, {}).get(key, {}):
                            if isinstance(call_session.get(entity, {}).get(key, {}).get(subkey, {}), dict):
                                for super_subkey in call_session.get(entity, {}).get(key, {}).get(subkey, {}):
                                    flattened_call_session[
                                        f"{entity}_{key}_{subkey}_{super_subkey}"
                                    ] = call_session.get(entity, {}).get(key, {}).get(subkey, {}).get(super_subkey)
                            else:
                                flattened_call_session[
                                    f"{entity}_{key}_{subkey}"
                                ] = call_session.get(entity, {}).get(key, {}).get(subkey)
                    else:
                        flattened_call_session[f"{entity}_{key}"] = call_session.get(entity, {}).get(key)

            flattened_call_sessions.append(flattened_call_session)

        return flattened_call_sessions

    except KeyError as e:
        # Handle any missing keys in the JSON
        raise Exception(f"Error while flattening call sessions: Missing key {e}")


def main(req: func.HttpRequest) -> func.HttpResponse:
    print("Python HTTP trigger function processed a request.")

    try:
        # Parse the request body JSON
        data = req.get_json()
        call_record_id = data["value"][0]["resourceData"]["id"]

        # Fetch the call record details
        access_token = get_access_token(
            "<TENANT_ID>",
            "<CLIENT_SECRET_ID>",
            "<CLINET_SECRET_KEY>",
        )
        headers = {"Authorization": "Bearer " + access_token}
        response = requests.get(
            "https://graph.microsoft.com/v1.0/communications/callRecords/"
            + call_record_id,
            headers=headers,
        )
        response.raise_for_status()  # Check for any HTTP errors
        call_record = response.json()

        # Fetch the call session details
        response = requests.get(
            "https://graph.microsoft.com/v1.0/communications/callRecords/"
            + call_record_id
            + "/sessions",
            headers=headers,
        )
        response.raise_for_status()  # Check for any HTTP errors
        sessions = response.json()["value"]

        call_record_flat = flatten_call_record(call_record)
        call_session_flat = flatten_call_sessions(sessions)

        # Database connection parameters
        server = "<>"
        database = "<>"
        driver = "{ODBC Driver 18 for SQL Server}"
        username = "<>"
        password = "<>"

        # Create the connection string
        connection_string = (
            "DRIVER="
            + driver
            + ";SERVER="
            + server
            + ";DATABASE="
            + database
            + ";Uid="
            + username
            + ";Pwd="
            + password
            + ";Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
        )

        print("Connecting to DB.")
        conn = pyodbc.connect(connection_string)

        cursor = conn.cursor()

        df_record = pd.DataFrame(call_record_flat)
        df_session = pd.DataFrame(call_session_flat)

        df_record = df_record.fillna(value="null")
        df_session = df_session.fillna(value="null")

        print("Inserting Records")
        for index, row in df_record.iterrows():
            columns = ', '.join(row.index)
            placeholders = ', '.join(['?'] * len(row))
            query = f"INSERT INTO dbo.call_record ({columns}) VALUES ({placeholders})"
            cursor.execute(query, row.values)


        column_mapping = {
            "callee_@odata.type": "callee_odatatype",
            "caller_userAgent_@odata.type": "caller_userAgent_odatatype",
            "callee_@odata.type": "callee_odatatype",
            "callee_userAgent_@odata.type": "callee_userAgent_odatatype",
        }

        for old_name, new_name in column_mapping.items():
            if old_name in df_session.columns:
                df_session.rename(columns={old_name: new_name}, inplace=True)
                df_session['primary_call_record_id'] = call_record_id

        for index, row in df_session.iterrows():
            columns = ', '.join(row.index)
            placeholders = ', '.join(['?'] * len(row))
            query = f"INSERT INTO dbo.call_session ({columns}) VALUES ({placeholders})"
            cursor.execute(query, row.values)

        # Commit the transaction and close the connection
        conn.commit()
        conn.close()

        return func.HttpResponse("Data inserted successfully.", status_code=200)

    except Exception as e:
        # Handle any other unexpected exceptions
        return func.HttpResponse(f"An error occurred: {e}", status_code=500)

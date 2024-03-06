import os, pickle, json

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from rich.console import Console
from rich.table import Table

# These are the Google API scopes your application has access to.
GOOGLE_SCOPES = ['https://www.googleapis.com/auth/presentations']
# BTW: If modifying these scopes, delete the file token.pickle in the folder local to the script.

# Path to the folder containing Google API credentials.
CRED_PATH = os.environ['GOOGLE_CREDENTIALS_FOLDER'] 

def read_credentials(folder_path):
    """
    Reads the Google API credentials from the specified folder path.
    Only files with .json extension are considered.
    Args:
        folder_path (str): The path to the folder containing the credentials files.
    Returns:
        list: A list of tuples containing the account type, account name, project ID, and file path for each credential file found.
    """
    credentials = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.json'):
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, 'r') as file:
                try:
                    data = json.load(file)
                    account_type = "Service Account" if "client_email" in data else "User Account"
                    account_name = data.get("client_email", "N/A")
                    project_id = data.get("project_id", "N/A")
                    credentials.append((account_type, account_name, project_id, file_path))
                except json.JSONDecodeError:
                    pass  # Not a valid JSON file, skip
    return credentials

def display_credentials(credentials):
    """
    Displays the Google API credentials in a table format.
    Asks the user to select the credentials to use.
    """
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Account Type", style="dim")
    table.add_column("Account Name")
    table.add_column("Project ID")
    table.add_column("File Path", style="green")

    for account_type, account_name, project_id, file_path in credentials:
        table.add_row(account_type, account_name, project_id, file_path)

    console = Console()
    console.print(table)

    selected_index = int(console.input("Select the index of credentials to use [bold yellow](e.g., 1):[/] ")) - 1
    return selected_index if 0 <= selected_index < len(credentials) else None

def authenticate_with_credentials(credentials, selected_index):
    """
    Authenticates with the Google API using the selected credentials.
    """
    creds = get_credentials(credentials_file=credentials[selected_index][3])
    service = build('slides', 'v1', credentials=creds)
    return service

def get_credentials(credentials_file):
    """
    Gets the Google API credentials from the specified file.
    If the credentials are not valid, it asks the user to log in.
    """
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file, GOOGLE_SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

def get_google_slides_service():
    """
    Gets the Google Slides service.
    Reads the credentials, asks the user to select one, and authenticates with the Google API.
    """
    credentials = read_credentials(CRED_PATH)

    if not credentials:
        print("No credentials files found.")
        return
    
    selected_index = display_credentials(credentials)

    if selected_index is not None:
        service = authenticate_with_credentials(credentials, selected_index)
    else:
        print("Invalid selection.")
    return service
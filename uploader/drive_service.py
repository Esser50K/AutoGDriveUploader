import apiclient
import os
import pickle
from copy import deepcopy
from google.auth.transport.requests import Request
from googleapiclient.discovery import build, MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow


FOLDER_MIMETYPE = "application/vnd.google-apps.folder"
SCOPES = ['https://www.googleapis.com/auth/drive'] # If modifying these scopes, delete the file token.pickle.

def get_credentials():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds

def build_request(http, *args, **kwargs):
    return apiclient.http.HttpRequest(deepcopy(http), *args, **kwargs)

class DriveService:
    instance = None

    def __init__(self, creds=None):
        if not DriveService.instance:
            DriveService.instance = build('drive', 'v3', credentials=creds, requestBuilder=build_request)

    def upload_folder(self, folder_name, parent_id=None):
        folder_metadata = {'name': folder_name,
                        'mimeType': FOLDER_MIMETYPE}
        if parent_id:
            folder_metadata['parents'] = [parent_id]
        
        return self.files().create(body=folder_metadata, fields="id").execute()

    def upload_file(self, file_name, file_path, parent_id=None):
        file_metadata = {'name': file_name}
        if parent_id:
            file_metadata['parents'] = [parent_id]

        media = MediaFileUpload(file_path,
                            resumable=True)
        file = self.files().create(
            body=file_metadata,
            media_body=media,
            fields='id')

        media.stream()
        response = None
        while response is None:
            try:
                status, response = file.next_chunk()
                if status:
                    print("Uploaded %d%% of %s." % (int(status.progress() * 100), file_name))
            except Exception as e:
                print("Error uploading file %s: %s" % (file_name, e))
                print("status info:", status)
        print("Upload of %s Complete!" % file_name)
        return response

    def __getattr__(self, attr):
        return getattr(DriveService.instance, attr)

    def __setattr__(self, name, value):
        return setattr(DriveService.instance, name, value)

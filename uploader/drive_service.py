import apiclient
import os
import pickle
import time
import json
from copy import deepcopy
from google.auth.transport.requests import Request
from googleapiclient.discovery import build, MediaFileUpload, HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from queue import Queue
from uploader.notification import RemoteScanNotification

FOLDER_MIMETYPE = "application/vnd.google-apps.folder"
# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']


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
            DriveService.instance = build(
                'drive', 'v3', credentials=creds, requestBuilder=build_request)

        self.cancel_uploads = {}

    def list_folder_deep(self, folder_gid, notification_queue=Queue(), depth=9999, all_items={}):
        last_remote_scan_file = folder_gid + "_scan.json"
        if os.path.isfile(last_remote_scan_file):
            with open(last_remote_scan_file, "r") as last_scan:
                all_items = json.loads(last_scan.read())

        return self._list_folder_deep(folder_gid, last_remote_scan_file, notification_queue, depth, all_items)

    def _list_folder_deep(self, folder_gid, filename, notification_queue=Queue(), depth=9999, all_items={}):
        if depth == 0:
            return self._write_and_notify(filename, all_items)

        depth -= 1
        for item in self.list_folder_items(folder_gid):
            item["gpid"] = folder_gid
            all_items[item["id"]] = item
            if item["mimeType"] == FOLDER_MIMETYPE:
                all_items = self._list_folder_deep(
                    item["id"], filename, notification_queue, depth, all_items)

        return self._write_and_notify(filename, all_items)

    def _write_and_notify(self, filename, items, notification_queue=Queue()):
        temp_file_name = ("%s_%s" % (filename, str(
            int(time.time())))).encode("utf-8") + ".json"
        with open(temp_file_name, "w") as lt:
            lt.write(json.dumps(items, indent=4))

        os.replace(temp_file_name, filename)
        notification_queue.put(RemoteScanNotification(items))
        return items

    def list_folder_items(self, folder_gid):
        return self.files().list(pageSize=1000, q="'%s' in parents" %
                                 folder_gid).execute()["files"]

    def upload_folder(self, folder_name, parent_gid=None):
        folder_metadata = {'name': folder_name,
                           'mimeType': FOLDER_MIMETYPE}
        if parent_gid:
            folder_metadata['parents'] = [parent_gid]

        return self.files().create(body=folder_metadata, fields="id").execute()

    def upload_file(self, file_id, file_name, file_path,
                    file_gid=None, parent_gid=None, progress_queue=Queue()):
        self.cancel_uploads[file_id] = False
        file_metadata = {'name': file_name}
        if parent_gid and not file_gid:
            file_metadata['parents'] = [parent_gid]

        max_retries = 5
        while max_retries != 0:
            try:
                os.rename(file_path, file_path)
                break
            except Exception as e:
                # File was probably in use so create a new upload request
                print("file still in use, waiting...", e)
                time.sleep(.5)
                max_retries -= 1

        file = None
        media = MediaFileUpload(file_path, resumable=True)
        if file_gid:
            file = self.files().update(
                fileId=file_gid,
                body=file_metadata,
                media_body=media,
                fields='id'
            )
        else:
            file = self.files().create(
                body=file_metadata,
                media_body=media,
                fields='id')
        media.stream()

        progress = 0
        response = None
        progress_queue.put({"progress": 0,
                            "in_failure": False})
        fail_count = 0
        while response is None and not self.is_canceled(file_id) and fail_count < 10:
            try:
                status, response = file.next_chunk()
                if status:
                    progress = status.progress()
                    print("Uploaded %d%% of %s." %
                          (int(progress * 100), file_name))
                    progress_queue.put({"progress": progress,
                                        "in_failure": False})
            except Exception as e:
                print("Error uploading file %s: %s" % (file_name, e))
                progress_queue.put({"progress": progress,
                                    "in_failure": True})
                time.sleep(.5)
                if type(e) is HttpError:
                    media = MediaFileUpload(file_path,
                                            resumable=True)
                    file = self.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields='id')
                    media.stream()
                    progress_queue.put({"progress": 0,
                                        "in_failure": True})
                fail_count += 1

        progress_queue.put(False)
        return response

    def move_file(self, old_doc, new_doc, old_tree, current_tree):
        file_id = new_doc["id"]
        file_gid = old_doc["gid"]
        file = self.service.files().get(fileId=file_gid,
                                        fields='parents').execute()
        old_folder_gids = ",".join(file.get('parents'))
        new_folder_gid = current_tree[current_tree[file_id]["pid"]]["gid"]
        file = self.service.files().update(fileId=file_gid,
                                           addParents=new_folder_gid,
                                           removeParents=old_folder_gids,
                                           fields='id, parents').execute()

    def is_canceled(self, file_id):
        return file_id in self.cancel_uploads.keys() and self.cancel_uploads[file_id]

    def cancel(self, file_id):
        if file_id in self.cancel_uploads.keys():
            self.cancel_uploads[file_id] = True

    def cancel_all(self):
        for f in self.cancel_uploads.keys():
            self.cancel_uploads[f] = True

    def __getattr__(self, attr):
        return getattr(DriveService.instance, attr)

    def __setattr__(self, name, value):
        return setattr(DriveService.instance, name, value)

import apiclient
import os
import pickle
import time
import json
from uploader.utils import find_children
from copy import deepcopy
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload
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

    def __init__(self, base_gid="", creds=None):
        if DriveService.instance:
            return

        DriveService.instance = build(
            'drive', 'v3', credentials=creds, requestBuilder=build_request)

        self.cancel_uploads = {}
        self.all_items = {}

        self.last_remote_scan_file = base_gid + "_scan.json"
        if os.path.isfile(self.last_remote_scan_file):
            with open(self.last_remote_scan_file, "r") as last_scan:
                self.all_items = json.loads(last_scan.read())

    def list_folder_deep(self, folder_gid, notification_queue=Queue(), depth=9999, all_items={}):
        return self._list_folder_deep(folder_gid, self.last_remote_scan_file, notification_queue, depth, self.all_items)

    def _list_folder_deep(self, folder_gid, filename, notification_queue=Queue(), depth=9999, all_items={}):
        if depth == 0:
            return self._write_and_notify(folder_gid, filename, all_items, notification_queue)

        depth -= 1

        folder_items = []
        try:
            folder_items = self.list_folder_items(folder_gid)
        except Exception as e:
            print("Error occurred trying to list items of:", folder_gid, e)

        folder_nodes = {}
        for item in folder_items:
            if "kind" in item:
                del item["kind"]

            item["gpid"] = folder_gid
            all_items[item["id"]] = item
            folder_nodes[item["id"]] = item
            if item["mimeType"] == FOLDER_MIMETYPE:
                all_items = self._list_folder_deep(
                    item["id"], filename, notification_queue, depth, all_items)

        all_items = {**self.all_items, **all_items}
        previous_children = find_children(folder_gid, all_items)
        deleted_or_moved = set(previous_children) - folder_nodes.keys()
        self.all_items = all_items
        for deleted in deleted_or_moved:
            del self.all_items[deleted]

        return self._write_and_notify(folder_gid, filename, all_items, notification_queue)

    def _write_and_notify(self, folder_gid, filename, items, notification_queue=Queue()):
        temp_file_name = ("%s_%s" % (filename, str(
            int(time.time())))) + ".json"
        with open(temp_file_name, "w") as lt:
            lt.write(json.dumps(items, indent=4))

        os.replace(temp_file_name, filename)
        notification_queue.put(RemoteScanNotification(folder_gid, items))
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
        print("uploading file at:", file_path)
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
        file = self.files().get(fileId=file_gid,
                                fields='parents').execute()
        old_folder_gids = ",".join(file.get('parents'))
        new_folder_gid = current_tree[current_tree[file_id]["pid"]]["gid"]
        file = self.files().update(fileId=file_gid,
                                   addParents=new_folder_gid,
                                   removeParents=old_folder_gids,
                                   fields='id, parents').execute()

    def download_file(self, file_id, destination_path, progress_queue=Queue()):
        request = self.files().get_media(fileId=file_id)
        with open(destination_path, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                try:
                    status, done = downloader.next_chunk()
                    if status:
                        progress_queue.put({"progress": status.progress()})
                except Exception as e:
                    print("Error downloading File %s: %s" % (file_id, e))
                    progress_queue.put({"progress": -1})
                    return

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

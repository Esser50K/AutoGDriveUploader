import sys
import json
import pickle
import os.path
from hashutils import hash_file, hash_string
from googleapiclient.discovery import build, MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

import httplib2
import apiclient

import time
from pprint import pprint

# Backup Settings
FILES_BLACKLIST = set([".DS_Store"])
folders_to_backup = ["/Users/esser420/Youtubing"]

# google drive specific constants
BASE_FOLDER = "Esser50kMacBackup"
BASE_FOLDER_GID_FILE = "base_id.json"
BASE_FOLDER_GID = ""
SCOPES = ['https://www.googleapis.com/auth/drive'] # If modifying these scopes, delete the file token.pickle.
FOLDER_MIMETYPE = "application/vnd.google-apps.folder"

# global service
service = None

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

def get_base_folder_id():
    # Create base folder if it does not exist yet
    folder_id = ""
    if BASE_FOLDER_GID_FILE not in os.listdir("."):
        folder_id = upload_folder(service, BASE_FOLDER)
        with open(BASE_FOLDER_GID_FILE, "w") as base_file:
            base_file.write(json.dumps({"name": BASE_FOLDER,
                                        "id": folder_id["id"]}))
    else:
        with open(BASE_FOLDER_GID_FILE, "r") as base_file:
            base_info = json.loads(base_file.read())
            folder_id = base_info["id"]

    return folder_id

def upload_folder(service, folder_name, parent_id=None):
    folder_metadata = {'name': folder_name,
                       'mimeType': FOLDER_MIMETYPE}
    if parent_id:
        folder_metadata['parents'] = [parent_id]
    
    print("uploading!!!!")
    return service.files().create(body=folder_metadata, fields="id").execute()

def upload_file(file_name, file_path, parent_id=None):
    file_metadata = {'name': file_name}
    if parent_id:
        file_metadata['parents'] = [parent_id]
    media = MediaFileUpload(file_path,
                        resumable=True)
    file = service.files().create(
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
    print("Upload of %s Complete!" % file_name)
    return response


def folder_doc(id, pid, name):
    return {"id": id,
            "pid": pid,
            "name": name,
            "folder": True}

def file_doc(id, pid, name, path):
    return {"id": id,
            "pid": pid,
            "name": name,
            "folder": False,
            "path": path}

def analyze_tree(folders_to_backup = []):
    old_tree = {}
    if "last_tree.json" in os.listdir("."):
        with open("last_tree.json", "r") as last:
            old_tree = json.loads(last.read())

    current_tree = {}
    for folder in folders_to_backup:
        for root, dirs, files in os.walk(folder):
            folder_id = hash_string(os.path.abspath(root).encode("utf-8"))
            folder_path = "/".join(root.split(os.sep)[:-1])
            parent_id = hash_string(folder_path.encode("utf-8"))
            folder_name = root.split(os.sep)[-1]
            current_tree[folder_id] = folder_doc(folder_id, parent_id, folder_name)

            for filename in files:
                if filename in FILES_BLACKLIST:
                    continue

                file_id = os.path.getsize(root + os.sep + filename)
                file_path = folder_path + "/" + folder_name + "/" + filename
                current_tree[str(file_id)] = file_doc(file_id, folder_id, filename, file_path)

    new_files = current_tree.keys() - old_tree.keys()
    deleted_files = old_tree.keys() - current_tree.keys()
    new_folders = set([f for f in new_files if current_tree[f]["folder"]])
    new_files = new_files - new_folders
    still_old = old_tree.keys() & current_tree.keys()
    print("DELETED:", deleted_files)


    renamed_files = []
    moved_files = []
    for k in still_old:
        if old_tree[k]["name"] != current_tree[k]["name"]:
            renamed_files.append(k)

        if old_tree[k]["pid"] != current_tree[k]["pid"]:
            moved_files.append(k)

    return {
        "old_tree": old_tree,
        "current_tree": current_tree,
        "new_folders": new_folders,
        "new_files": new_files,
        "renamed_files": renamed_files,
        "moved_files": moved_files,
        "deleted_files": deleted_files
    }

def _upload_folders(base_folder_gid, folder_doc, current_tree):
    global service
    folder_pid = folder_doc["pid"]

    if "gid" in folder_doc.keys():
        return folder_doc["gid"]

    # if the parent folder id is not in the 
    # current tree it means it's in the root of the project
    # so we can upload it directly
    if folder_pid not in current_tree.keys() and "gid" not in folder_doc.keys():
        print("uploading folder %s to root" % folder_doc["name"])
        result = upload_folder(service, folder_doc["name"], base_folder_gid)
        gid = result["id"]
        current_tree[folder_doc["id"]]["gid"] = gid
        return gid

    if folder_pid in current_tree.keys() and "gid" not in current_tree[folder_pid].keys():
        gid = _upload_folders(base_folder_gid, current_tree[folder_pid], current_tree)
        current_tree[folder_pid]["gid"] = gid

    print("uploading '%s' to '%s' with GID %s" % (folder_doc["name"], current_tree[folder_pid]["name"], current_tree[folder_pid]["gid"]))
    result = upload_folder(service, folder_doc["name"], current_tree[folder_pid]["gid"])
    gid = result["id"]
    current_tree[folder_doc["id"]]["gid"] = gid
    return gid

def upload_folders(base_folder_gid, new_folder_ids, current_tree, old_tree):
    merged_trees = {**current_tree, **old_tree}
    for folder_id in new_folder_ids:
        folder_doc = current_tree[folder_id]
        print("trying upload for %s" % folder_doc["name"])
        #_upload_folders([], base_folder_gid, folder_doc, current_tree)
        folder_doc["gid"] = _upload_folders(base_folder_gid, folder_doc, merged_trees)
        merged_trees[folder_id] = folder_doc
    return merged_trees

def upload_files(new_file_ids, current_tree):
    pool = ThreadPoolExecutor(max_workers=10)
    for file_id in new_file_ids:
        pool.submit(upload_file_job, file_id, current_tree)

    pool.shutdown()
    return current_tree

def upload_file_job(file_id, current_tree):
    file_doc = current_tree[file_id]
    folder_doc = current_tree[file_doc["pid"]]
    print("uploading file %s to folder %s" % (file_doc["name"], folder_doc["name"]))
    result = upload_file(file_doc["name"], file_doc["path"], folder_doc["gid"])
    file_doc["gid"] = result["id"]
    current_tree[file_id] = file_doc


# TODO: This will have to be for another "feature" there will be sink mode which just uploads new files, sync mode actually syncs folders
# TODO: Create function to list create tree from upstream if base_id.json exists
# Also the folder hash should have the root as if it is in googles base folder so that it's easy to match them here
# Should have one tree to reflect upstream, other is the last saved one, other is current
# when deciding to upload a file. If file is same size, check if name changed also check last modified (in case somebody just corrected a single letter typo)
# maybe need to also index files by name so one can update modified text files. Or check the mime type (if size is different but name and size are different its probably still same file)
# even better is to ID file by inode (not sure if that works on windows): 
# os.stat('path/to/file').st_ino


def create_tree_from_drive(service, base_folder_id, base_folder_name):
    result = service.files().list(q='"%s" in parents' % base_folder_id,
                                fields="files(id,name,size,pageToken)")
    for files in result["files"]:
        # Recursively check other folders
        # keep list of lists of files (can use size to id)
        pass


def build_request(http, *args, **kwargs):
    return apiclient.http.HttpRequest(deepcopy(http), *args, **kwargs)

if __name__ == "__main__":
    if "credentials.json" not in os.listdir("."):
        print("You have to first download the credentials.json file and place it in this folder.")
        print("You can download it from: https://developers.google.com/drive/api/v3/quickstart/python")
        sys.exit(1)

    creds = get_credentials()

    # Override the requestBuilder internally to always create new httplib object for safe multithreaded use
    service = build('drive', 'v3', credentials=creds, requestBuilder=build_request)
    BASE_FOLDER_GID = get_base_folder_id()

    tree_analysis = analyze_tree(folders_to_backup)
    pprint(tree_analysis)

    current_tree = upload_folders(BASE_FOLDER_GID, tree_analysis["new_folders"], tree_analysis["current_tree"], tree_analysis["old_tree"])
    upload_files(tree_analysis["new_files"], current_tree)

    with open("last_tree.json", "w") as tree:
        new_ids = list(tree_analysis["new_folders"]) + list(tree_analysis["new_files"])
        print("new ids:", new_ids)
        new_files_tree = {id: tree_analysis["current_tree"][id] \
                            for id in (new_ids) \
                                if tree_analysis["current_tree"][id].get("gid", False)}
        new_tree = {**tree_analysis["current_tree"], **tree_analysis["old_tree"]}
        for k in tree_analysis["deleted_files"]:
            del new_tree[k]
        tree.write(json.dumps(new_tree, indent=4))

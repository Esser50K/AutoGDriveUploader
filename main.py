import os
import json
from queue import Queue
from uploader.event_handler import DirectoryChangeEventHandler
from uploader.watcher import DirectoryWatcher
from uploader.drive_service import DriveService, get_credentials
from time import sleep


BASE_FOLDER = "Esser50kMacBackup"
BASE_FOLDER_GID_FILE = "base_id.json"


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

ROOT_PATH = "/Users/esser420/Youtubing"

if __name__ == "__main__":
    notification_queue = Queue()
    base_gid = get_base_folder_id()

    creds = get_credentials()
    DriveService(creds)  # initiate thread-safe drive service singleton

    dw = DirectoryWatcher(base_gid, ROOT_PATH, notification_queue)
    dw.start()

    input()

    dw.stop()

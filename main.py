import asyncio
import os
import sys
import json
from queue import Queue
from uploader.event_handler import DirectoryChangeEventHandler
from uploader.watcher import DirectoryWatcher
from uploader.drive_service import DriveService, get_credentials
from uploader.server import UploaderInfoServer
from time import sleep
from threading import Thread

BASE_FOLDER = "Esser50kMacBackup"
BASE_FOLDER_GID_FILE = "base_id.json"


def get_base_folder_id():
    # Create base folder if it does not exist yet
    folder_id = ""
    if BASE_FOLDER_GID_FILE not in os.listdir("."):
        folder_id = DriveService().upload_folder(BASE_FOLDER)
        with open(BASE_FOLDER_GID_FILE, "w") as base_file:
            base_file.write(json.dumps({"name": BASE_FOLDER,
                                        "id": folder_id["id"]}))
    else:
        with open(BASE_FOLDER_GID_FILE, "r") as base_file:
            base_info = json.loads(base_file.read())
            folder_id = base_info["id"]

    return folder_id


ROOT_PATH = "/Users/esser420/Youtubing"
#ROOT_PATH = "/Users/esser420/Pictures/GoPro"

ROOT_PATHS = ["/Users/esser420/Youtubing",
              "/Users/esser420/Pictures/GoPro"]

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        notification_queue = Queue()
        creds = get_credentials()
        base_gid = get_base_folder_id()

        # initiate thread-safe drive service singleton
        driveService = DriveService(creds)
        remote_file_sync_notifications = Queue()
        directory_watcher = DirectoryWatcher(
            base_gid, ROOT_PATHS, notification_queue)
        server = UploaderInfoServer(
            "localhost", 6900, directory_watcher, remote_file_sync_notifications, loop)
        server.start()
        directory_watcher.process_events()
        loop.run_until_complete(server.server_start)
        loop.run_forever()
    except Exception as e:
        print("Got interrupted by:", e.with_traceback(sys.exc_info()[2]))
        server.stop()
    except KeyboardInterrupt:
        server.stop()

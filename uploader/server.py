import os
import json
import asyncio
import subprocess
import platform
from queue import Queue
from uploader.notification import *
from uploader.drive_service import DriveService
from uploader.watcher import DirectoryWatcher
from websockets import WebSocketServerProtocol as WS, serve
from threading import Thread, Lock
from time import sleep


class UploaderInfoServer:
    def __init__(self, host: str, port: int, watcher: DirectoryWatcher, remote_scan_notifications: Queue, event_loop):
        self.loop = event_loop
        self.server_start = serve(self.root_handler, host, port)
        self.current_tree_status = {}
        self.remote_tree_status = {}
        self.watcher = watcher
        self.notification_queue = watcher.notification_queue
        self.remote_notification_queue = remote_scan_notifications
        self.full_tree_clients = {}
        self.tree_status_clients = {}
        self.remote_tree_status_clients = {}
        self.file_notification_getter = None
        self.remote_notification_getter = None
        self.notification_lock = Lock()

    async def root_handler(self, websocket: WS, uri: str):
        if uri.endswith("/full"):
            with self.notification_lock:
                self.full_tree_clients[websocket.remote_address] = websocket
            await websocket.send(json.dumps({"idx": self.watcher.current_tree_idx, "names": self.watcher.all_tree_names(), "tree": self.watcher.current_tree()}))
        elif uri.endswith("/status"):
            with self.notification_lock:
                self.tree_status_clients[websocket.remote_address] = websocket
            await websocket.send(json.dumps(self.remote_tree_status))
        elif uri.endswith("/remote"):
            with self.notification_lock:
                self.remote_tree_status_clients[websocket.remote_address] = websocket
            await websocket.send(json.dumps({"root": "", "tree": self.remote_tree_status}))
        elif uri.endswith("/command"):
            await self.handle_commands(websocket)
        else:
            print("client tried to connect on:", uri)
            await websocket.close()
            return

        await websocket.wait_closed()
        if uri.endswith("/full"):
            del self.full_tree_clients[websocket.remote_address]
        elif uri.endswith("/status"):
            del self.tree_status_clients[websocket.remote_address]
        elif uri.endswith("/status"):
            del self.remote_tree_status_clients[websocket.remote_address]

    async def handle_commands(self, websocket: WS):
        while not websocket.closed:
            command = await websocket.recv()
            cmd = json.loads(command)
            if cmd["type"] == "CHANGE_DIR":
                self.watcher.set_current_tree(cmd["tree_idx"])
                for client in self.full_tree_clients.values():
                    await client.send(json.dumps({"idx": self.watcher.current_tree_idx, "names": self.watcher.all_tree_names(), "tree": self.watcher.current_tree()}))
            elif cmd["type"] == "SYNC_FOLDER":
                if "id" not in cmd.keys():
                    continue

                if str(cmd["id"]) in self.watcher.current_tree().keys() and "gid" in self.watcher.current_tree()[str(cmd["id"])]:
                    gid = self.watcher.current_tree()[str(cmd["id"])]["gid"]
                    Thread(target=DriveService().list_folder_deep, args=(
                        self.watcher.base_gid, gid, self.remote_notification_queue, 1,)).start()
                    continue

                if str(cmd["id"]) in self.remote_tree_status.keys():
                    gid = self.remote_tree_status[str(cmd["id"])]["id"]
                    Thread(target=DriveService().list_folder_deep, args=(
                        self.watcher.base_gid, gid, self.remote_notification_queue, 1,)).start()
                    continue

            elif cmd["type"] == "OPEN_FILE":
                if "id" not in cmd.keys() or str(cmd["id"]) not in self.watcher.current_tree().keys():
                    continue

                filepath = self.watcher.current_tree()[str(cmd["id"])]["path"]
                if platform.system() == 'Darwin':
                    subprocess.call(('open', filepath))
                elif platform.system() == 'Windows':
                    # pylint: disable=no-member
                    os.startfile(filepath)
                else:
                    subprocess.call(('xdg-open', filepath))

    def get_file_notifications(self):
        while True:
            notification = self.notification_queue.get()
            if not notification:
                break

            self.parse_and_apply_notification(notification)
            print("GOT NOTIFICATION:", notification)
            with self.notification_lock:
                for client in self.full_tree_clients.values():
                    asyncio.run_coroutine_threadsafe(client.send(
                        json.dumps({"idx": self.watcher.current_tree_idx, "names": self.watcher.all_tree_names(), "tree": self.watcher.current_tree()})), self.loop)

                for client in self.tree_status_clients.values():
                    asyncio.run_coroutine_threadsafe(client.send(
                        json.dumps(self.current_tree_status)), self.loop)

    def get_remote_notifications(self):
        while True:
            notification = self.remote_notification_queue.get()
            if not notification:
                break

            self.parse_and_apply_remote_notification(notification)
            # print("GOT REMOTE NOTIFICATION:", notification)
            with self.notification_lock:
                for client in self.remote_tree_status_clients.values():
                    asyncio.run_coroutine_threadsafe(client.send(
                        json.dumps({"root": notification.root, "tree": self.remote_tree_status})), self.loop)

    def parse_and_apply_notification(self, notification: Notification):
        file_id = notification.file_doc["id"]
        if notification.type == FILE_CREATED_NOTIFICATION \
           or notification.type == FILE_UPDATED_NOTIFICATION \
           or notification.type == FILE_DELETED_NOTIFICATION:
            if file_id in self.current_tree_status.keys():
                # if the file is not in the status tree it is considered uploaded
                del self.current_tree_status[file_id]
        elif notification.type == FILE_UPLOAD_PROGRESS_NOTIFICATION:
            self.current_tree_status[file_id] = {"progress": notification.progress,
                                                 "in_failure": notification.in_failure}

        filedoc = notification.file_doc

        """
        TODO: Somehow notify of local file deletion so it can be rendered without scanning the remote tree
        I should probbably populate the remote tree automatically with the files/folders that have a gid

        if notification.type == FILE_DELETED_NOTIFICATION \
                and "gid" in filedoc.keys() \
                and filedoc["gid"] not in self.remote_tree_status.keys():
            current_tree = self.watcher.current_tree()
            parent = current_tree()[
                filedoc["pid"]] if filedoc["pid"] in current_tree() else ""
            self.remote_tree_status[filedoc["gid"]] = {
                "id": filedoc["gid"],
                "name": filedoc["name"],
                "mimeType": filedoc["mimeType"],
                "gpid": }
        """

    def parse_and_apply_remote_notification(self, notification: RemoteScanNotification):
        self.remote_tree_status = notification.remote_files

    def start(self):
        self.file_notification_getter = Thread(
            target=self.get_file_notifications)
        self.file_notification_getter.start()
        self.remote_notification_getter = Thread(
            target=self.get_remote_notifications)
        self.remote_notification_getter.start()
        self.watcher.start()

    def stop(self):
        self.watcher.stop()
        self.notification_queue.put(None)
        self.file_notification_getter.join()

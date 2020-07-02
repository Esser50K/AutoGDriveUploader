import json
import asyncio
from queue import Queue
from uploader.notification import *
from uploader.watcher import DirectoryWatcher
from websockets import WebSocketServerProtocol as WS, serve
from threading import Thread
from time import sleep

class UploaderInfoServer:
    def __init__(self, host: str, port: int, watcher: DirectoryWatcher, event_loop):
        self.loop = event_loop
        self.server_start = serve(self.root_handler, host, port)
        self.current_tree_status = {}
        self.watcher = watcher
        self.notification_queue = watcher.notification_queue
        self.full_tree_clients = {}
        self.tree_status_clients = {}
        self.notification_getter = None

    async def root_handler(self, websocket: WS, uri: str):
        if uri.endswith("/full"):
            self.full_tree_clients[websocket.remote_address] = websocket
            await websocket.send(json.dumps(self.watcher.current_tree()))
        elif uri.endswith("/status"):
            self.tree_status_clients[websocket.remote_address] = websocket
        else:
            print("client tried to connect on:", uri)
            await websocket.close()
            return

        await websocket.wait_closed()
        if uri.endswith("/full"):
            del self.full_tree_clients[websocket.remote_address]
        elif uri.endswith("/status"):
            del self.tree_status_clients[websocket.remote_address]

    def get_notifications(self):
        while True:
            notification = self.notification_queue.get()
            if not notification:
                break

            self.parse_and_apply_notification(notification)
            print("GOT NOTIFICATION:", notification)
            for client in self.full_tree_clients.values():
                asyncio.run_coroutine_threadsafe(client.send(json.dumps(self.watcher.current_tree())), self.loop)

            for client in self.tree_status_clients.values():
                asyncio.run_coroutine_threadsafe(client.send(json.dumps(self.current_tree_status)), self.loop)

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

    def start(self):
        self.notification_getter = Thread(target=self.get_notifications)
        self.notification_getter.start()
        self.watcher.start()

    def stop(self):
        self.watcher.stop()
        self.notification_queue.put(None)
        self.notification_getter.join()

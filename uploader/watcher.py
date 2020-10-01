from queue import Queue
from watchdog.observers import Observer
from uploader.event_handler import DirectoryChangeEventHandler
from threading import Thread


class DirectoryWatcher(Thread):
    def __init__(self, base_gid, root_paths, notification_queue: Queue):
        self.current_selected_tree = root_paths[0]
        self.base_gid = base_gid
        self.root_paths = root_paths
        self.notification_queue = notification_queue
        self.event_handlers = {path: DirectoryChangeEventHandler(
            base_gid, path, notification_queue) for path in root_paths}
        self.event_observer = Observer()
        self.running = False
        self.notification_alert = None

    def start(self, notification_alert=False):
        for event_handler in self.event_handlers.values():
            event_handler.start()
            self.event_observer.schedule(
                event_handler,
                event_handler.root_path,
                recursive=True
            )
        self.event_observer.start()
        self.running = True
        if notification_alert:
            self.notification_alert = Thread(target=self.notification_printer)
            self.notification_alert.start()

    def stop(self):
        self.event_observer.stop()
        for event_handler in self.event_handlers.values():
            event_handler.stop()
        self.event_observer.join()
        for event_handler in self.event_handlers.values():
            event_handler.join()
        self.running = False
        self.notification_queue.put(None)
        if self.notification_alert:
            self.notification_alert.join()

    def update_root_paths(self, root_paths):
        added_root_paths = set(root_paths) - set(self.root_paths)
        removed_root_paths = set(self.root_paths) - set(root_paths)
        self.root_paths = list(root_paths)

        # remove event handlers that are not watching any new root paths
        for path in removed_root_paths:
            self.event_handlers[path].stop()
            self.event_handlers[path].join()
            del self.event_handlers[path]

            if path == self.current_selected_tree:
                self.current_selected_tree = self.root_paths[0] if len(
                    self.root_paths) > 0 else ""

        # add new event handlers
        for path in added_root_paths:
            self.event_handlers[path] = DirectoryChangeEventHandler(
                self.base_gid, path, self.notification_queue)
            self.event_handlers[path].start()

        if self.current_selected_tree not in self.root_paths and len(self.root_paths) > 0:
            self.current_selected_tree = self.root_paths[0]

    def current_tree(self):
        return self.event_handlers[self.current_selected_tree].current_tree

    def current_tree_name(self):
        return self.current_selected_tree.split("/")[-1]

    def set_current_tree(self, idx):
        self.current_selected_tree = idx

    def get_next_notification(self):
        return self.notification_queue.get()

    def notification_printer(self):
        while self.running:
            print(self.get_next_notification())

    def process_events(self):
        for event_handler in self.event_handlers.values():
            t = Thread(target=event_handler.process_event)
            t.daemon = True
            t.start()

    def prepare_download(self, file_gid, remote_tree):
        event_handler = self.event_handlers[self.current_selected_tree]
        return event_handler.prepare_download(file_gid, remote_tree)

    def download_file(self, file_gid, to_create_file):
        event_handler = self.event_handlers[self.current_selected_tree]
        event_handler.download_file(
            file_gid, to_create_file)

    def clean_trees(self):
        for handler in self.event_handlers.values():
            handler.clean_tree()

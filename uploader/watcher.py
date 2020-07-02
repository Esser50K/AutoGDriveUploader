from queue import Queue
from watchdog.observers import Observer
from uploader.event_handler import DirectoryChangeEventHandler
from threading import Thread


class DirectoryWatcher(Thread):
    def __init__(self, base_gid, root_path, notification_queue: Queue):
        self.base_gid = base_gid
        self.root_path = root_path
        self.notification_queue = notification_queue
        self.event_handler = DirectoryChangeEventHandler(base_gid, root_path, notification_queue)
        self.event_observer = Observer()
        self.running = False
        self.notification_alert = None

    def start(self, notification_alert=False):
        self.event_handler.start()
        self.event_observer.schedule(
            self.event_handler,
            self.root_path,
            recursive=True
        )
        self.event_observer.start()
        self.running = True
        if notification_alert:
            self.notification_alert = Thread(target=self.notification_printer)
            self.notification_alert.start()

    def stop(self):
        self.event_observer.stop()
        self.event_handler.stop()
        self.event_observer.join()
        self.event_handler.join()
        self.running = False
        self.notification_queue.put(None)
        if self.notification_alert:
            self.notification_alert.join()

    def current_tree(self):
        return self.event_handler.current_tree

    def get_next_notification(self):
        return self.notification_queue.get()

    def notification_printer(self):
        while self.running:
            print(self.get_next_notification())
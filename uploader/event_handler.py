import os
import json
from copy import deepcopy
from queue import Queue
from uploader.hashutils import hash_file, hash_string
from concurrent.futures import ThreadPoolExecutor
from threading import Thread, Lock
from watchdog.events import FileSystemEventHandler
from uploader.drive_service import DriveService


FILES_BLACKLIST = set([".DS_Store"])

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

class DirectoryChangeEventHandler(FileSystemEventHandler, Thread):
    def __init__(self, base_folder_gid, root_path, notification_queue):
        self.base_folder_gid = base_folder_gid
        self.root_path = root_path
        self.notification_queue = notification_queue
        self.last_tree_id_file = hash_string(root_path.encode("utf-8")) + "_last.json"
        self.current_tree = self.load_last_tree()
        self.event_queue = Queue()
        self.uploader = ThreadPoolExecutor(max_workers=10)
        self.service = DriveService()
        self.tree_lock = Lock()
        super().__init__()

    def on_any_event(self, event):
        self.event_queue.put(event)

    def stop(self):
        self.event_queue.put(None)

    def run(self):
        # start processing queue
        while self.event_queue.get() is not None:
            self.process_event()

    def process_event(self):
        old_tree = deepcopy(self.current_tree)
        tree_analysis = self.analyze_tree()

        # first upload folders then files will have the folder gid to be uploaded to
        self.current_tree = self.upload_folders(tree_analysis["new_folders"], tree_analysis["current_tree"])
        self.update_tree(self.current_tree)
        self.move_files(tree_analysis["moved_files"], tree_analysis["old_tree"], self.current_tree)
        self.update_tree(self.current_tree)
        self.upload_files(tree_analysis["new_files"], self.current_tree)
        self.update_tree(self.current_tree)

    def add_gid(self, doc_id, gid):
        if doc_id not in self.current_tree.keys():
            print("There is no %s in the current tree." % doc_id)
            return

        with self.tree_lock:
            self.current_tree[doc_id]["gid"] = gid
            self.save_tree(self.current_tree)

    def update_tree(self, tree):
        with self.tree_lock:
            self.current_tree = tree
            self.save_tree(tree)

    def save_tree(self, tree):
        with open(self.last_tree_id_file, "w") as lt:
            lt.write(json.dumps(tree, indent=4))

    def analyze_tree(self):
        new_tree = {}
        for root, dirs, files in os.walk(self.root_path):
            try:
                folder_id = hash_string(os.path.abspath(root).encode("utf-8"))
                folder_path = "/".join(root.split(os.sep)[:-1])
                parent_id = hash_string(folder_path.encode("utf-8"))
                folder_name = root.split(os.sep)[-1]
                new_tree[folder_id] = folder_doc(folder_id, parent_id, folder_name)

                for filename in files:
                    if filename in FILES_BLACKLIST:
                        continue

                    try:
                        file_id = os.stat(root + os.sep + filename).st_ino
                        file_path = folder_path + "/" + folder_name + "/" + filename
                        new_tree[str(file_id)] = file_doc(file_id, folder_id, filename, file_path)
                    except Exception as e:
                        print("error on getting info for file:", e)
            except Exception as e:
                print("error while walking through tree:", e)

        new_files = new_tree.keys() - self.current_tree.keys()
        deleted_files = self.current_tree.keys() - new_tree.keys()
        new_folders = set([f for f in new_files if new_tree[f]["folder"]])
        new_files = new_files - new_folders
        still_old = self.current_tree.keys() & new_tree.keys()

        renamed_files = []
        moved_files = []
        for k in still_old:
            if self.current_tree[k]["name"] != new_tree[k]["name"]:
                renamed_files.append(k)

            if self.current_tree[k]["pid"] != new_tree[k]["pid"]:
                moved_files.append(k)
                
        # copy gids if they exist
        for k, v in self.current_tree.items():
            if k in new_tree.keys() and "gid" in self.current_tree[k].keys():
                new_tree[k]["gid"] = self.current_tree[k]["gid"]

        return {
            "old_tree": self.current_tree,
            "current_tree": new_tree,
            "new_folders": new_folders,
            "new_files": new_files,
            "renamed_files": renamed_files,
            "moved_files": moved_files,
            "deleted_files": deleted_files
        }

    def load_last_tree(self):
        last_tree = {}
        if self.last_tree_id_file in os.listdir("."):
            with open(self.last_tree_id_file, "r") as last:
                last_tree = json.loads(last.read())

        return last_tree

    def _upload_folders(self, folder_doc, current_tree):
        folder_pid = folder_doc["pid"]

        if "gid" in folder_doc.keys():
            return folder_doc["gid"]

        # if the parent folder id is not in the 
        # current tree it means it's in the root of the project
        # so we can upload it directly
        if folder_pid not in current_tree.keys() and "gid" not in folder_doc.keys():
            print("uploading folder %s to root" % folder_doc["name"])
            result = self.service.upload_folder(folder_doc["name"], self.base_folder_gid)
            return result["id"]

        if folder_pid in current_tree.keys() and "gid" not in current_tree[folder_pid].keys():
            gid = _upload_folders(self.base_folder_gid, current_tree[folder_pid], current_tree)
            current_tree[folder_pid]["gid"] = gid

        print("uploading '%s' to '%s' with GID %s" % (folder_doc["name"], current_tree[folder_pid]["name"], current_tree[folder_pid]["gid"]))
        result = self.service.upload_folder(folder_doc["name"], current_tree[folder_pid]["gid"])
        return result["id"]

    def upload_folders(self, new_folder_ids, new_tree):
        for folder_id in new_folder_ids:
            folder_doc = current_tree[folder_id]
            print("trying upload for %s" % folder_doc["name"])
            folder_doc["gid"] = _upload_folders(self.base_folder_gid, folder_doc, new_tree)
            new_tree[folder_id] = folder_doc
        return new_tree

    def upload_files(self, new_file_ids, current_tree):
        for file_id in new_file_ids:
            self.uploader.submit(self.upload_file_job, file_id, current_tree)

        return current_tree

    def upload_file_job(self, file_id, current_tree):
        file_doc = current_tree[file_id]
        folder_doc = current_tree[file_doc["pid"]]
        print("uploading file %s to folder %s" % (file_doc["name"], folder_doc["name"]))
        try:
            result = self.service.upload_file(file_doc["name"], file_doc["path"], folder_doc["gid"])
        except Exception as e:
            print("unrecoverable error uploading file %s:" % file_doc["name"], e)
            return
            
        self.add_gid(file_id, result["id"])

    def move_files(self, moved_files, old_tree, current_tree):
        for file_id in moved_files:
            old_doc = old_tree[file_id]
            new_doc = current_tree[file_id]
            print(old_doc)
            print(new_doc)
            print("moving file %s from %s to %s" % (old_doc["name"],
                                                    old_tree[old_doc["pid"]]["name"],
                                                    current_tree[new_doc["pid"]]["name"]))
            try:
                file_gid = old_doc["gid"]
                file = self.service.files().get(fileId=file_gid,
                                                fields='parents').execute()
                old_folder_gids = ",".join(file.get('parents'))
                new_folder_gid = current_tree[current_tree[file_id]["pid"]]["gid"]
                file = self.service.files().update(fileId=file_gid,
                                                   addParents=new_folder_gid,
                                                   removeParents=old_folder_gids,
                                                   fields='id, parents').execute()
                print("successfuly moved file %s from %s to %s" % (old_doc["name"],
                                                                old_tree[old_doc["pid"]]["name"],
                                                                current_tree[new_doc["pid"]]["name"]))
            except Exception as e:
                print("error moving file:", old_doc)
                print(e)


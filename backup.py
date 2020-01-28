import os
import json
from hashutils import hash_file, hash_string

BASE_FOLDER = "Esser50kMacBackup"
FILES_BLACKLIST = set([".DS_Store"])

folders_to_backup = ["/Users/esser420/Youtubing"]


current_tree = {}
for folder in folders_to_backup:
    print("Backing up %s" % folder)
    for root, dirs, files in os.walk(folder):
        print("In %s folder" % root)
        folder_id = hash_string(os.path.abspath(root).encode("utf-8"))
        parent_id = hash_string("".join(root.split(os.sep)[:-1]).encode("utf-8"))
        name = root.split(os.sep)[-1]
        current_tree[folder_id] = {
            "id": folder_id,
            "pid": parent_id,
            "name": name,
            "folder": True
        }

        for filename in files:
            if filename in FILES_BLACKLIST:
                continue
            
            print("found file: %s" % filename)
            file_id = hash_file(root + os.sep + filename)
            current_tree[file_id] = {
                "id": file_id,
                "pid": folder_id,
                "name": filename,
                "folder": False
            }

with open("last_tree.json", "w") as tree:
    tree.write(json.dumps(current_tree, indent=4))
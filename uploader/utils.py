import os
import json


def find_children(pid, tree):
    return set([j["id"] for j in tree.values() if j["gpid"] == pid])


def find_all_children(pid, tree, children=[]):
    children = find_children(pid, tree)
    for child in children:
        if child["folder"]:
            children.extend(find_children(child["id"], tree))
    return children


def read_sync_folders():
    with open("sync_folders.json", "r") as sffile:
        return json.load(sffile)


def write_sync_folders(sync_folders):
    with open("sync_folders_temp.json", "w") as sffile:
        sffile.write(json.dumps(sync_folders, indent=2))

    os.rename("sync_folders_temp.json", "sync_folders.json")

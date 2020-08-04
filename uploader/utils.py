def find_children(pid, tree):
    return set([j["id"] for j in tree.values() if j["gpid"] == pid])


def find_all_children(pid, tree, children=[]):
    children = find_children(pid, tree)
    for child in children:
        if child["folder"]:
            children.extend(find_children(child["id"], tree))
    return children

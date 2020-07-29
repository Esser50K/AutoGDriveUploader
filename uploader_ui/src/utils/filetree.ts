import {
  FileTreeModel,
  FileTreeNodeModel,
  RemoteFileTreeModel,
  RemoteFileTreeNodeModel,
} from "../models/filetree";
import { FileLocation } from "../components/FileTree/consts";

const FOLDER_MIMETYPE = "application/vnd.google-apps.folder";

export const findChildren = (
  pid: string,
  fullTree: FileTreeModel
): FileTreeNodeModel[] => {
  return Object.values(fullTree).filter((node: any) => node.pid === pid);
};

const findAllChildren = (
  pid: string,
  tree: FileTreeModel
): FileTreeNodeModel[] => {
  const children = findChildren(pid, tree);
  for (let child of children) {
    if (child.folder) {
      children.push(...findAllChildren(child.id, tree));
    }
  }

  return children;
};

export const findChildrenWithMap = (
  pid: string,
  gpid: string,
  fullTree: FileTreeModel,
  remoteTree: RemoteFileTreeModel,
  parentToChildren: { [key: string]: string[] },
  remoteParentToChildren: { [key: string]: string[] },
  localGidToNode: { [key: string]: FileTreeNodeModel }
): FileTreeNodeModel[] => {
  const start = performance.now()

  const localChildrenIds = pid in parentToChildren
    ? parentToChildren[pid]
    : [];
  const remoteChildrenIds = gpid in remoteParentToChildren
    ? remoteParentToChildren[gpid]
    : [];

  const localChildren = localChildrenIds
    .map((id) => fullTree[id])
    .filter((node) => node !== undefined);

  const remoteChildren = remoteChildrenIds
    .map((id) => remoteTree[id])
    .filter((node) => node !== undefined);

  for (let rchild of remoteChildren) {
    if (rchild.id in localGidToNode) {
      continue;
    }

    localChildren.push(remoteToLocal(rchild));
  }

  return localChildren;
};

export const parentToChildrenMap = (
  fullTree: FileTreeModel
): { [key: string]: string[] } => {
  const children: { [key: string]: string[] } = {};
  for (let node of Object.values(fullTree)) {
    if (!(node.pid in children)) {
      children[node.pid] = [];
    }

    children[node.pid].push(node.id);
  }

  return children;
};

export const createLocalLookupTables = (
  fullTree: FileTreeModel
): [{ [key: string]: string[] }, { [key: string]: FileTreeNodeModel }] => {
  const children: { [key: string]: string[] } = {};
  const gidNodes: { [key: string]: FileTreeNodeModel } = {};
  for (let node of Object.values(fullTree)) {
    if (!(node.pid in children)) {
      children[node.pid] = [];
    }

    if (node.gid && !(node.gid in gidNodes)) {
      gidNodes[node.gid] = node;
    }

    children[node.pid].push(node.id);
  }

  return [children, gidNodes];
};

export const createRemoteLookupTables = (
  remoteTree: RemoteFileTreeModel
): [
    { [key: string]: string[] },
    { [key: string]: RemoteFileTreeNodeModel }
  ] => {
  const children: { [key: string]: string[] } = {};
  const gidNodes: { [key: string]: RemoteFileTreeNodeModel } = {};
  for (let node of Object.values(remoteTree)) {
    if (!(node.gpid in children)) {
      children[node.gpid] = [];
    }

    if (node.id && !(node.id in gidNodes)) {
      gidNodes[node.id] = node;
    }

    children[node.gpid].push(node.id);
  }

  return [children, gidNodes];
};

export const findRemoteChildren = (
  gpid: string,
  remoteTree: RemoteFileTreeModel
): RemoteFileTreeNodeModel[] => {
  return Object.values(remoteTree).filter((node) => node.gpid === gpid);
};

export const findActive = (tree: FileTreeModel): FileTreeNodeModel[] => {
  return Object.values(tree).filter((node: any) => node.active);
};

export const findRootId = (tree: FileTreeModel): string => {
  return Object.values(tree).find(
    (node: any): node is any => !(node.pid in tree)
  )?.id;
};

export const populateTree = (
  pid: string,
  tree: FileTreeModel
): FileTreeNodeModel => {
  const children = findChildren(pid, tree);

  const childrenNodes = children.map((child: FileTreeNodeModel) => {
    return populateTree(child.id, tree);
  });

  return {
    id: pid,
    pid: pid,
    gid: tree[pid]?.gid,
    name: tree[pid]?.name,
    folder: tree[pid]?.folder || false,
    active: tree[pid]?.active,
    toggled: tree[pid]?.toggled === undefined ? true : tree[pid]?.toggled,
    children: childrenNodes.length === 0 ? undefined : childrenNodes,
  };
};

export const getLocation = (node: FileTreeNodeModel): FileLocation =>
  node.id !== node.gid
    ? node.gid
      ? FileLocation.Both
      : FileLocation.OnlyLocal
    : FileLocation.OnlyRemote;

export const getBackgroundColor = (location: FileLocation): string =>
  location === FileLocation.Both
    ? "node-color-both"
    : location === FileLocation.OnlyRemote
      ? "node-color-remote"
      : "node-color-local";

export const remoteToLocal = (
  node: RemoteFileTreeNodeModel
): FileTreeNodeModel => {
  return {
    id: node.id,
    gid: node.id,
    pid: node.gpid,
    gpid: node.gpid,
    name: node.name,
    folder: node.mimeType === FOLDER_MIMETYPE,
  };
};

export const remoteToLocalWithMap = (
  node: RemoteFileTreeNodeModel,
  gidToNode: { [key: string]: FileTreeNodeModel }
): FileTreeNodeModel => {
  const id = node.id in gidToNode
    ? gidToNode[node.id].id
    : node.id;
  const pid = node.gpid in gidToNode
    ? gidToNode[node.gpid].id
    : node.gpid;

  return {
    id: id,
    gid: node.id,
    pid: pid,
    gpid: node.gpid,
    name: node.name,
    folder: node.mimeType === FOLDER_MIMETYPE,
  };
};

export const mergeTrees = (
  localTree: FileTreeModel,
  remoteTree: RemoteFileTreeModel
): FileTreeModel => {
  const mergedTree: FileTreeModel = { ...localTree };
  for (let remoteFile of Object.values(remoteTree)) {
    const local = remoteToLocal(remoteFile);
    mergedTree[local.id] = local;
  }

  return mergedTree;
};

export const mergeTreesWithMap = (
  localTree: FileTreeModel,
  remoteTree: RemoteFileTreeModel
): FileTreeModel => {
  const mergedTree: FileTreeModel = { ...localTree };
  for (let remoteFile of Object.values(remoteTree)) {
    const local = remoteToLocal(remoteFile);
    mergedTree[local.id] = local;
  }

  return mergedTree;
};

export const abbreviateSize = (value: number) => {
  let newValue = value.toString();
  if (value >= 1000) {
    const suffixes = ["b", "kb", "mb", "gb", "tb"];
    const suffixNum = Math.floor(("" + value).length / 3);
    let shortValue = 0;
    for (let precision = 2; precision >= 1; precision--) {
      shortValue = parseFloat(
        (suffixNum !== 0
          ? value / Math.pow(1000, suffixNum)
          : value
        ).toPrecision(precision)
      );
      const dotLessShortValue = shortValue
        .toString()
        .replace(/[^a-zA-Z 0-9]+/g, "");
      if (dotLessShortValue.length <= 2) {
        break;
      }
    }

    let shortValString = shortValue.toString();
    if (shortValue % 1 !== 0) {
      shortValString = shortValue.toFixed(1);
    }
    newValue = shortValString + suffixes[suffixNum];
  }
  return newValue;
};

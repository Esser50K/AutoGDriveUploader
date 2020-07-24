import { FileTreeModel, FileTreeNodeModel } from "../models/filetree";

export const findChildren = (
  pid: string,
  tree: FileTreeModel
): FileTreeNodeModel[] => {
  return Object.values(tree).filter((node: any) => node.pid === pid);
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

export const mergeTrees = (
  origTree: FileTreeModel,
  newTree: FileTreeModel
): FileTreeModel => {
  Object.entries(newTree).forEach(([key, value]) => {
    if (!(key in origTree)) {
      origTree[key] = value;
    }
  });

  const toRemove: string[] = [];
  Object.entries(origTree).forEach(([key, value]) => {
    if (!(key in newTree)) {
      toRemove.push(key);
    }
  });
  toRemove.forEach((id) => delete origTree[id]);

  return origTree;
};

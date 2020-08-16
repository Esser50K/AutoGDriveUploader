import { atom } from "recoil";
import { FileTreeNodeModel, RemoteFileTreeNodeModel } from "../models/filetree";

export type NodeState = {
  open: boolean;
};

export const nodesState = atom<{ [key: string]: NodeState }>({
  key: "nodesState",
  default: {},
});

export const selectedNodeState = atom({
  key: "selectedNodeState",
  default: "",
});

export const openFileState = atom({
  key: "openFileState",
  default: "",
});

export const selectedFolderIdState = atom({
  key: "selectedFolderIdState",
  default: "",
});

export const loadingFolderIdState = atom({
  key: "loadingFoldersIdState",
  default: new Set(),
});

export const downloadFileIdState = atom({
  key: "downloadFileIdState",
  default: "",
});

export const downloadFolderIdState = atom({
  key: "downloadFolderIdState",
  default: "",
});

export const currentRootState = atom({
  key: "currentRootState",
  default: "",
});

export const parentToChildrenState = atom<{ [key: string]: string[] }>({
  key: "parentToChildrenState",
  default: {},
});

export const remoteParentToChildrenState = atom<{ [key: string]: string[] }>({
  key: "remoteParentToChildrenState",
  default: {},
});

export const gidToNodeState = atom<{ [key: string]: FileTreeNodeModel }>({
  key: "gidToNodeState",
  default: {},
});

export const remoteGidToNodeState = atom<{
  [key: string]: RemoteFileTreeNodeModel;
}>({
  key: "remoteGidToNodeState",
  default: {},
});

export const selectedSyncFolderState = atom<number>({
  key: "selectedSyncFolderState",
  default: -1
})

export const availableSyncFoldersState = atom<string[]>({
  key: "availableSyncFoldersState",
  default: []
})
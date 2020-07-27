export type FileTreeNodeModel = {
  id: string;
  pid: string;
  gid?: string;
  gpid?: string;
  name: string;
  folder: boolean;
  last_modified?: number;
  path?: string;
  size?: number;

  // display attributes (to change)
  active?: boolean;
  toggled?: boolean;
  children?: FileTreeNodeModel[];
};

export type FileTreeModel = {
  [key: string]: FileTreeNodeModel;
};

export type RemoteFileTreeNodeModel = {
  id: string;
  gpid: string;
  name: string;
  mimeType: string;
};

export type RemoteFileTreeModel = {
  [key: string]: RemoteFileTreeNodeModel;
};

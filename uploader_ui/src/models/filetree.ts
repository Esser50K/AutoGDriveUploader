export type FileTreeNodeModel = {
  id: string;
  pid: string;
  gid: string;
  name: string;
  folder: boolean;
  last_modified?: number;
  path?: string;

  // display attributes (to change)
  active?: boolean;
  toggled?: boolean;
  children?: FileTreeNodeModel[];
};

export type FileTreeModel = {
  [key: string]: FileTreeNodeModel;
};

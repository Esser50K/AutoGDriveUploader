import React, { MouseEvent, useState, useEffect } from "react";
import {
  FileTreeNodeModel,
  FileTreeModel,
  RemoteFileTreeModel,
} from "../models/filetree";
import {
  findChildren,
  findRemoteChildren,
  getLocation,
  getBackgroundColor,
  remoteToLocal,
  findChildrenWithMap,
} from "../utils/filetree";
import FileTreeFile from "./FileTreeFile";
import "./FileTree.css";
import { useRecoilState } from "recoil";
import {
  nodesState,
  parentToChildrenState,
  gidToNodeState,
  remoteGidToNodeState,
  remoteParentToChildrenState,
} from "../states/filetree";

interface FileTreeProps {
  treeNode: FileTreeNodeModel;
  fullTree: FileTreeModel;
  uploadStatusTree: FileTreeModel; // not really file tree model
  remoteTree: RemoteFileTreeModel;
}

const FileTreeFolder = (props: FileTreeProps) => {
  const [children, setChildren] = useState<FileTreeNodeModel[]>([]);
  const [currentNodesState, setNodesState] = useRecoilState(nodesState);
  const [parentToChildren] = useRecoilState(parentToChildrenState);
  const [remoteParentToChildren] = useRecoilState(remoteParentToChildrenState);
  const [gidToNode] = useRecoilState(gidToNodeState);

  const onClick = (event: MouseEvent<HTMLLIElement, globalThis.MouseEvent>) => {
    event.preventDefault();
    event.stopPropagation();
    setNodesState((oldNodesState) => {
      const newNodesState = { ...oldNodesState };
      const newCurrentNodeState = { ...oldNodesState[props.treeNode.id] };
      newCurrentNodeState.open = !newCurrentNodeState.open;
      newNodesState[props.treeNode.id] = newCurrentNodeState;
      return newNodesState;
    });
  };

  const location = getLocation(props.treeNode);
  const background = getBackgroundColor(location);
  const isOpen = currentNodesState[props.treeNode.id]?.open;
  const childrenCss = isOpen ? "non-root-folder show" : "non-root-folder";
  const imageUrl = isOpen ? "open-folder.png" : "closed-folder.png";

  /*
  const children = isOpen
    ? findChildren(props.treeNode.id, props.fullTree)
    : [];
  const childrenMap: { [key: string]: FileTreeNodeModel } = {};
  for (let child of children) {
    childrenMap[child.id] = child;
  }

  const remoteChildren =
    isOpen && props.treeNode.gid
      ? findRemoteChildren(props.treeNode.gid, props.remoteTree)
      : [];

  console.info("remote CHILDREN:", remoteChildren);

  for (let child of remoteChildren) {
    const local = remoteToLocal(child, props.fullTree);
    childrenMap[local.id] = local;
  }
  */

  useEffect(() => {
    (async () => {
      const nextChildren = isOpen
        ? findChildrenWithMap(
          props.treeNode.id,
          props.treeNode.gid || "",
          props.fullTree,
          props.remoteTree,
          parentToChildren,
          remoteParentToChildren,
          gidToNode
        )
        : []
      setChildren(nextChildren)
    })()
  }, [isOpen, props, parentToChildren, remoteParentToChildren, gidToNode])

  return (
    <div className="node-container folder-container">
      <li
        className={`node folder-node ${background}`}
        onClick={(e) => {
          onClick(e);
        }}
      >
        <img
          src={process.env.PUBLIC_URL + `/icons/${imageUrl}`}
          alt="open or closed folder icon"
          className="open-folder-icon"
        />
        <div>
          <div className="node-content-title-line">
            <div className="node-element node-title">
              <b>{props.treeNode.name}</b>
            </div>
          </div>
          <div className="node-content-status-line">
            <div className="node-element node-upload-status">
              {"UPLOADED: " + (props.treeNode.gid !== undefined)}
            </div>
          </div>
        </div>
      </li>
      <ul className={childrenCss}>
        {Object.values(children).map((node) => {
          return node.folder ? (
            <FileTreeFolder
              key={node.id}
              treeNode={node}
              fullTree={props.fullTree}
              remoteTree={props.remoteTree}
              uploadStatusTree={props.uploadStatusTree}
            ></FileTreeFolder>
          ) : (
              <FileTreeFile key={node.id} treeNode={node}></FileTreeFile>
            );
        })}
      </ul>
    </div>
  );
};

export default FileTreeFolder;

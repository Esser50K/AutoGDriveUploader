import React, { useEffect, useState, MouseEvent } from "react";
import {
  FileTreeNodeModel,
  FileTreeModel,
  RemoteFileTreeModel,
} from "../models/filetree";
import { findChildren } from "../utils/filetree";
import FileTreeFile from "./FileTreeFile";
import "./FileTree.css";
import { useRecoilState } from "recoil";
import { nodesState } from "../states/filetree";

interface FileTreeProps {
  treeNode: FileTreeNodeModel;
  fullTree: FileTreeModel;
  uploadStatusTree: FileTreeModel; // not really file tree model
  remoteTree: RemoteFileTreeModel;
}

const FileTreeFolder = (props: FileTreeProps) => {
  const [currentNodesState, setNodesState] = useRecoilState(nodesState);

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

  const isOpen = currentNodesState[props.treeNode.id]?.open;
  const childrenCss = isOpen ? "non-root-folder show" : "non-root-folder";
  const children = isOpen
    ? findChildren(props.treeNode.id, props.fullTree)
    : [];
  const imageUrl = isOpen ? "open-folder.png" : "closed-folder.png";
  return (
    <div className="node-container folder-container">
      <li
        className="node folder-node"
        onClick={(e) => {
          onClick(e);
        }}
      >
        <img
          src={process.env.PUBLIC_URL + `/icons/${imageUrl}`}
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
        {children.map((node) => {
          return node.folder ? (
            <FileTreeFolder
              treeNode={node}
              fullTree={props.fullTree}
              remoteTree={props.remoteTree}
              uploadStatusTree={props.uploadStatusTree}
            ></FileTreeFolder>
          ) : (
            <FileTreeFile treeNode={node}></FileTreeFile>
          );
        })}
      </ul>
    </div>
  );
};

export default FileTreeFolder;

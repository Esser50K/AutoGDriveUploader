import React, { useEffect, useState, MouseEvent } from "react";
import { FileTreeNodeModel, FileTreeModel } from "../models/filetree";
import { findChildren } from "../utils/filetree";
import FileTreeFile from "./FileTreeFile";
import "./FileTree.css";

interface FileTreeProps {
  treeNode: FileTreeNodeModel;
  fullTree: FileTreeModel;
  isOpen?: boolean;
}

const FileTreeFolder = (props: FileTreeProps) => {
  const isOpen = props.isOpen !== undefined ? props.isOpen : false;
  const [open, setOpen] = useState(isOpen);

  const onClick = (event: MouseEvent<HTMLLIElement, globalThis.MouseEvent>) => {
    event.preventDefault();
    event.stopPropagation();
    setOpen(!open);
  };

  const childrenCss = open ? "non-root-folder show" : "non-root-folder";
  const children = open ? findChildren(props.treeNode.id, props.fullTree) : [];
  const imageUrl = open ? "open-folder.png" : "closed-folder.png";
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

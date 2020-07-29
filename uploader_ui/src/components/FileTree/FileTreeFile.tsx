import React from "react";
import { FileTreeNodeModel } from "../../models/filetree";
import "./FileTree.css";
import {
  abbreviateSize,
  getLocation,
  getBackgroundColor,
} from "../../utils/filetree";

interface FileTreeProps {
  treeNode: FileTreeNodeModel;
}

const FileTreeFile = (props: FileTreeProps) => {
  const onClick = (event: React.MouseEvent<HTMLLIElement, MouseEvent>) => {
    event.preventDefault();
    event.stopPropagation();
  };

  const location = getLocation(props.treeNode);
  const background = getBackgroundColor(location);
  return (
    <div className="node-container file-container">
      <li
        className={`node file-node ${background}`}
        onClick={(e) => onClick(e)}
      >
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
            {props.treeNode.size && (
              <div className="node-element node-last-modified">
                {"SIZE: " + abbreviateSize(props.treeNode.size)}
              </div>
            )}
          </div>
        </div>
      </li>
    </div>
  );
};

export default FileTreeFile;

import React from "react";
import { FileTreeNodeModel, FileTreeModel } from "../../models/filetree";
import "./FileTree.css";
import {
  abbreviateSize,
  getLocation,
  getBackgroundColor,
} from "../../utils/filetree";
import { useRecoilState, useSetRecoilState } from "recoil";
import { selectedNodeState, openFileState, downloadFileIdState } from "../../states/filetree";
import { iconFiletypeMap, FileLocation } from "./consts";
import ProgressBar from "../ProgressBar/ProgressBar";
import ActionButton from "./ActionButton";

interface FileTreeProps {
  treeNode: FileTreeNodeModel;
  uploadStatusTree: FileTreeModel;
}

const FileTreeFile = (props: FileTreeProps) => {
  const [selectedNodeId, setSelectedNodeId] = useRecoilState(selectedNodeState);
  const setDownloadFileId = useSetRecoilState(downloadFileIdState);
  const openFile = useSetRecoilState(openFileState);

  const onClick = (event: React.MouseEvent<HTMLLIElement, MouseEvent>) => {
    event.preventDefault();
    event.stopPropagation();
    setSelectedNodeId(() => props.treeNode.id)
  };

  const onDoubleClick = (event: React.MouseEvent<HTMLLIElement, MouseEvent>) => {
    openFile(() => props.treeNode.id)
  };

  const getIconName = (filename: string): string => {
    const extensionSplit = filename.split(".")
    const extension = extensionSplit[extensionSplit.length - 1]
    return extension in iconFiletypeMap ? iconFiletypeMap[extension] : "default-file";
  }

  const location = getLocation(props.treeNode);
  const background = getBackgroundColor(location);
  const nodeSelected = props.treeNode.id === selectedNodeId ? "node-selected" : "";
  const icon = getIconName(props.treeNode.name) + ".png"
  const uploadProgress = props.uploadStatusTree[props.treeNode.id]?.progress;

  return (
    <div className="node-container file-container">
      <li
        className={`node file-node ${background} ${nodeSelected}`}
        onClick={(e) => onClick(e)}
        onDoubleClick={(e) => onDoubleClick(e)}
      >
        <img
          src={process.env.PUBLIC_URL + `/icons/${icon}`}
          alt="icon representing filename"
          className="node-icon"
        />
        <div className="node-content">
          <div className="node-content-left">
            <div className="node-content-title-line">
              <div className="node-element node-title">
                <b>{props.treeNode.name}</b>
              </div>
              <div className="node-properties">
                {props.treeNode.size ? (
                  <div className="node-element node-property">
                    {props.treeNode.size !== 0 && <em>{abbreviateSize(props.treeNode.size)}</em>}
                  </div>
                ) : ""}
              </div>
            </div>
            <div className="node-content-action-line">
              {location === FileLocation.OnlyRemote &&
                <ActionButton text="DOWNLOAD" callback={() => { setDownloadFileId(props.treeNode.gid!) }}></ActionButton>}
            </div>
          </div>
          {uploadProgress !== undefined && uploadProgress !== 100 && uploadProgress !== 0 &&
            <div className="node-content-right">
              <ProgressBar progress={uploadProgress || 0}></ProgressBar>
            </div>}
        </div>
      </li>
    </div>
  );
};

export default FileTreeFile;

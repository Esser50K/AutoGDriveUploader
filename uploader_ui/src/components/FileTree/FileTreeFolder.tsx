import React, { MouseEvent, useState, useEffect } from "react";
import {
  FileTreeNodeModel,
  FileTreeModel,
  RemoteFileTreeModel,
} from "../../models/filetree";
import {
  getLocation,
  getBackgroundColor,
  findChildrenWithMap,
} from "../../utils/filetree";
import FileTreeFile from "./FileTreeFile";
import "./FileTree.css";
import { useRecoilState, useSetRecoilState } from "recoil";
import {
  nodesState,
  parentToChildrenState,
  gidToNodeState,
  remoteParentToChildrenState,
  selectedNodeState,
  currentRootState,
  selectedFolderIdState,
} from "../../states/filetree";

interface FileTreeProps {
  treeNode: FileTreeNodeModel;
  fullTree: FileTreeModel;
  uploadStatusTree: FileTreeModel; // not really file tree model
  remoteTree: RemoteFileTreeModel;
}

const FileTreeFolder = (props: FileTreeProps) => {
  const [children, setChildren] = useState<FileTreeNodeModel[]>([]);
  const [currentNodesState, setNodesState] = useRecoilState(nodesState);
  const [selectedNodeId, setSelectedNodeId] = useRecoilState(selectedNodeState);
  const setRootId = useSetRecoilState(currentRootState);
  const setSelectedFolderId = useSetRecoilState(selectedFolderIdState);
  const [parentToChildren] = useRecoilState(parentToChildrenState);
  const [remoteParentToChildren] = useRecoilState(remoteParentToChildrenState);
  const [gidToNode] = useRecoilState(gidToNodeState);

  const onClick = (event: MouseEvent<HTMLLIElement, globalThis.MouseEvent>) => {
    event.preventDefault();
    event.stopPropagation();
    setSelectedNodeId(() => props.treeNode.id)
    setSelectedFolderId(() => props.treeNode.id)
    setNodesState((oldNodesState) => {
      const newNodesState = { ...oldNodesState };
      const newCurrentNodeState = { ...oldNodesState[props.treeNode.id] };
      newCurrentNodeState.open = !newCurrentNodeState.open
      newNodesState[props.treeNode.id] = newCurrentNodeState;
      return newNodesState;
    });
  };

  const onDoubleClick = (event: MouseEvent<HTMLLIElement, globalThis.MouseEvent>) => {
    event.preventDefault();
    event.stopPropagation();
    setRootId(props.treeNode.id);
  }

  const location = getLocation(props.treeNode);
  const background = getBackgroundColor(location);
  const nodeSelected = props.treeNode.id === selectedNodeId ? "node-selected" : "";
  const isOpen = currentNodesState[props.treeNode.id]?.open;
  const imageUrl = isOpen ? "open-folder.png" : "closed-folder.png";

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
        className={`node folder-node ${background} ${nodeSelected}`}
        onClick={(e) => {
          onClick(e);
        }}
        onDoubleClick={(e) => {
          onDoubleClick(e);
        }}
      >
        <img
          src={process.env.PUBLIC_URL + `/icons/${imageUrl}`}
          alt="open or closed folder icon"
          className="node-icon"
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
      <ul className={`non-root-folder ${isOpen && "show"}`}>
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
        <div className={`folder-loader ${isOpen && "show"}`}>
          <li>
            <div className="loader center">
              <i className="fa fa-cog fa-spin" />
            </div>
          </li>
        </div>
      </ul>
    </div>
  );
};

export default FileTreeFolder;

import React, { useEffect, useState } from "react";
import FileTreeFile from "./FileTreeFile";
import FileTreeFolder from "./FileTreeFolder";
import { FileTreeModel, RemoteFileTreeModel } from "../models/filetree";
import { findRootId, findChildren } from "../utils/filetree";
import "./FileTree.css";

const FileTree = () => {
  const [rootId, setRootId] = useState<string>("");
  const [fullTree, setFullTree] = useState<FileTreeModel>({} as FileTreeModel);
  const [uploadStatusTree, setUploadStatusTree] = useState<FileTreeModel>(
    {} as FileTreeModel
  );
  const [remoteStateTree, setRemoteStateTree] = useState<RemoteFileTreeModel>(
    {} as RemoteFileTreeModel
  );

  useEffect(() => {
    const fullTreeState = new WebSocket("ws://localhost:6900/full");
    const uploadTreeState = new WebSocket("ws://localhost:6900/status");
    const remoteTreeState = new WebSocket("ws://localhost:6900/remote");

    fullTreeState.onmessage = (message: MessageEvent) => {
      const tree = JSON.parse(message.data);
      const rootId = findRootId(tree);
      setFullTree(tree);
      setRootId(rootId);
    };

    uploadTreeState.onmessage = (message: MessageEvent) => {
      setUploadStatusTree(JSON.parse(message.data));
    };

    remoteTreeState.onmessage = (message: MessageEvent) => {
      setRemoteStateTree(JSON.parse(message.data));
    };
  }, []);

  const children = findChildren(rootId, fullTree);
  console.info("CHILDREN:", children);
  return (
    <ul className="root-folder">
      {rootId && (
        <>
          {children.map((node) => {
            return node.folder ? (
              <FileTreeFolder
                treeNode={node}
                fullTree={fullTree}
                uploadStatusTree={uploadStatusTree}
                remoteTree={remoteStateTree}
              ></FileTreeFolder>
            ) : (
              <FileTreeFile treeNode={node}></FileTreeFile>
            );
          })}
        </>
      )}
    </ul>
  );
};

export default FileTree;

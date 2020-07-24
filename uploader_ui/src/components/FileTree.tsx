import React, { useEffect, useState } from "react";
import FileTreeFile from "./FileTreeFile";
import FileTreeFolder from "./FileTreeFolder";
import { FileTreeModel } from "../models/filetree";
import { findRootId, findChildren } from "../utils/filetree";
import "./FileTree.css";

const FileTree = () => {
  const [rootId, setRootId] = useState<string>("");
  const [fullTree, setFullTree] = useState<FileTreeModel>({} as FileTreeModel);
  const [stateTree, setStateTree] = useState<FileTreeModel>(
    {} as FileTreeModel
  );

  useEffect(() => {
    const fullTreeState = new WebSocket("ws://localhost:6900/full");
    const uploadTreeState = new WebSocket("ws://localhost:6900/status");

    fullTreeState.onmessage = (message: MessageEvent) => {
      const tree = JSON.parse(message.data);
      const rootId = findRootId(tree);
      setFullTree(tree);
      setRootId(rootId);
    };

    uploadTreeState.onmessage = (message: MessageEvent) => {
      setStateTree(JSON.parse(message.data));
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

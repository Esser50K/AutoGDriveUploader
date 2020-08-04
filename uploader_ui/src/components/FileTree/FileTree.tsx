import React, { useEffect, useState } from "react";
import FileTreeFile from "./FileTreeFile";
import FileTreeFolder from "./FileTreeFolder";
import {
  FileTreeModel,
  RemoteFileTreeModel,
  FileTreeNodeModel,
} from "../../models/filetree";
import {
  findRootId,
  findChildrenWithMap,
  createLocalLookupTables,
  createRemoteLookupTables,
} from "../../utils/filetree";
import "./FileTree.css";
import { useRecoilState, useSetRecoilState } from "recoil";
import {
  parentToChildrenState,
  gidToNodeState,
  remoteGidToNodeState,
  remoteParentToChildrenState,
  currentRootState,
  loadingFolderIdState,
} from "../../states/filetree";

const fullTreeState = new WebSocket("ws://localhost:6900/full");
const uploadTreeState = new WebSocket("ws://localhost:6900/status");
const remoteTreeState = new WebSocket("ws://localhost:6900/remote");

const FileTree = () => {
  const [children, setChildren] = useState<FileTreeNodeModel[]>([]);
  const [fullTree, setFullTree] = useState<FileTreeModel>({} as FileTreeModel);
  const [uploadStatusTree, setUploadStatusTree] = useState<FileTreeModel>({});
  const [remoteTree, setRemoteTree] = useState<RemoteFileTreeModel>({});
  const [rootId, setRootId] = useRecoilState(currentRootState);
  const [parentToChildren, setParentToChildren] = useRecoilState(
    parentToChildrenState
  );
  const [remoteParentToChildren, setRemoteParentToChildren] = useRecoilState(
    remoteParentToChildrenState
  );
  const [gidToNode, setGidToNode] = useRecoilState(gidToNodeState);
  const setLoadingFolderId = useSetRecoilState(loadingFolderIdState);
  const setRemotGidToNode = useSetRecoilState(
    remoteGidToNodeState
  );

  const parseAndApplyLocal = (data: string) => {
    const tree = JSON.parse(data);
    setFullTree(tree);

    if (rootId === "" || !(rootId in tree)) {
      setRootId(findRootId(tree));
    }

    const [parentToChildrenMap, gidToNodeMap] = createLocalLookupTables(tree);
    setParentToChildren(() => parentToChildrenMap);
    setGidToNode(gidToNodeMap);

    const nextChildren = findChildrenWithMap(
      rootId,
      tree[rootId]?.gid || "",
      tree,
      remoteTree,
      parentToChildrenMap,
      remoteParentToChildren,
      gidToNodeMap);
    setChildren(nextChildren);
  };

  const parseAndApplyRemote = async (data: string) => {
    const remoteTreeUpdate = JSON.parse(data);
    console.info(remoteTreeUpdate);
    const currentRemoteTree = remoteTreeUpdate.tree;
    setRemoteTree(currentRemoteTree);
    setLoadingFolderId((previousLoadingFolder) => {
      previousLoadingFolder.delete(remoteTreeUpdate.root)
      return previousLoadingFolder
    })

    const [parentToChildrenMap, gidToNodeMap] = createRemoteLookupTables(
      currentRemoteTree
    );
    setRemoteParentToChildren(parentToChildrenMap);
    setRemotGidToNode(gidToNodeMap);
  };

  useEffect(() => {
    fullTreeState.onmessage = (message: MessageEvent) => {
      parseAndApplyLocal(message.data);
    };

    remoteTreeState.onmessage = (message: MessageEvent) => {
      parseAndApplyRemote(message.data);
    };

    uploadTreeState.onmessage = (message: MessageEvent) => {
      setUploadStatusTree(JSON.parse(message.data));
    };

    const nextChildren = findChildrenWithMap(
      rootId,
      fullTree[rootId]?.gid || "",
      fullTree,
      remoteTree,
      parentToChildren,
      remoteParentToChildren,
      gidToNode)
    setChildren(nextChildren);
  }, [rootId, fullTree, remoteTree, parentToChildren, remoteParentToChildren, gidToNode]);

  useEffect(() => {
    const handleUserInput = (e: any) => {
      if (e.ctrlKey && e.key === 'ArrowUp') {
        const currentRoot = fullTree[rootId]
        if (currentRoot && currentRoot.pid in fullTree) {
          setRootId(currentRoot.pid)
        }
      }
    }

    document.addEventListener('keydown', handleUserInput);
    return () => {
      document.removeEventListener('keydown', handleUserInput)
    }
  }, [rootId, fullTree])

  return (
    <ul className="root-folder">
      {rootId && (
        <>
          {children.map((node) => {
            return node.folder ? (
              <FileTreeFolder
                key={node.id}
                treeNode={node}
                fullTree={fullTree}
                remoteTree={remoteTree}
                uploadStatusTree={uploadStatusTree}
              ></FileTreeFolder>
            ) : (
                <FileTreeFile key={node.id} treeNode={node}></FileTreeFile>
              );
          })}
        </>
      )}
    </ul>
  );
};

export default FileTree;

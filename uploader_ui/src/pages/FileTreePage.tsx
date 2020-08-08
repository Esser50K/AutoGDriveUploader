import React, { useEffect } from "react";
import FileTree from "../components/FileTree/FileTree";
import "./FileTreePage.css";
import NavBar from "../components/NavBar/NavBar";
import { useRecoilState } from "recoil";
import { selectedSyncFolderState, openFileState, selectedFolderIdState, availableSyncFoldersState } from "../states/filetree";

const commandSocket = new WebSocket("ws://localhost:6900/command");

const FileTreePage = () => {
    const [selectedSyncFolder] = useRecoilState(selectedSyncFolderState);
    const [openFileId, setOpenFileId] = useRecoilState(openFileState);
    const [selectedFolderId] = useRecoilState(selectedFolderIdState);
    const [availableSyncFolders] = useRecoilState(availableSyncFoldersState);
    useEffect(() => {
        if (commandSocket.readyState !== commandSocket.OPEN) {
            return
        }

        commandSocket.send(JSON.stringify({ "type": "CHANGE_DIR", "tree_idx": selectedSyncFolder }))
    }, [selectedSyncFolder])

    useEffect(() => {
        if (commandSocket.readyState !== commandSocket.OPEN || openFileId === "") {
            return
        }

        commandSocket.send(JSON.stringify({ "type": "OPEN_FILE", "id": openFileId }))
        setOpenFileId(() => "")
    }, [openFileId, setOpenFileId])

    useEffect(() => {
        if (commandSocket.readyState !== commandSocket.OPEN || selectedFolderId === "") {
            return
        }

        commandSocket.send(JSON.stringify({ "type": "SYNC_FOLDER", "id": selectedFolderId }))
    }, [selectedFolderId])

    return (
        <div className="app">
            <NavBar title="UPLOADER" syncFolders={availableSyncFolders}></NavBar>
            <div className="filetree-container">
                <FileTree></FileTree>
            </div>
        </div>
    );
};

export default FileTreePage;

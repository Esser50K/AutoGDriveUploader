import React, { useEffect } from "react";
import FileTree from "../components/FileTree/FileTree";
import "./FileTreePage.css";
import NavBar from "../components/NavBar/NavBar";
import { useRecoilState } from "recoil";
import { selectedSyncFolderState, openFileState } from "../states/filetree";

const commandSocket = new WebSocket("ws://localhost:6900/command");

const FileTreePage = () => {
    const [selectedFolder] = useRecoilState(selectedSyncFolderState);
    const [openFileId, setOpenFileId] = useRecoilState(openFileState);

    useEffect(() => {
        if (commandSocket.readyState === commandSocket.OPEN) {
            commandSocket.send(JSON.stringify({ "type": "CHANGE_DIR", "tree_idx": selectedFolder }))
        }
    }, [selectedFolder])

    useEffect(() => {
        if (commandSocket.readyState !== commandSocket.OPEN || openFileId === "") {
            console.info("OUTTA HERE")
            return
        }

        console.info("SENDING")
        commandSocket.send(JSON.stringify({ "type": "OPEN_FILE", "id": openFileId }))
        setOpenFileId(() => "")
    }, [openFileId])

    return (
        <div className="app">
            <NavBar title="UPLOADER" syncFolders={["Youtubing", "GoPro"]}></NavBar>
            <div className="filetree-container">
                <FileTree></FileTree>
            </div>
        </div>
    );
};

export default FileTreePage;

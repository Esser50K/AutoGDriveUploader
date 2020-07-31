import React, { useEffect } from "react";
import FileTree from "../components/FileTree/FileTree";
import "./FileTreePage.css";
import NavBar from "../components/NavBar/NavBar";
import { useRecoilState } from "recoil";
import { selectedSyncFolderState } from "../states/filetree";

const commandSocket = new WebSocket("ws://localhost:6900/command");

const FileTreePage = () => {
    const [selectedFolder] = useRecoilState(selectedSyncFolderState);

    useEffect(() => {
        if (commandSocket.readyState === commandSocket.OPEN) {
            commandSocket.send(JSON.stringify({ "type": "CHANGE_DIR", "tree_idx": selectedFolder }))
        }
    }, [selectedFolder])

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

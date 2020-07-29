import React from "react";
import FileTree from "../components/FileTree/FileTree";
import "./FileTreePage.css";
import NavBar from "../components/NavBar/NavBar";

const FileTreePage = () => {
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

import React from "react";
import FileTree from "../components/FileTree";
import "./FileTreePage.css";

const FileTreePage = () => {
    return (
        <div className="app">
            <div className="navbar">
                <h1>Uploader UI</h1>
            </div>
            <div className="filetree-container">
                <FileTree></FileTree>
            </div>
        </div>
    );
};

export default FileTreePage;

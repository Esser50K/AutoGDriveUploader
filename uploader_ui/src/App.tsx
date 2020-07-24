import React from "react";
import FileTree from "./components/FileTree";
import "./App.css";

const App = () => {
  return (
    <div className="app">
      <h1>Uploader UI</h1>
      <div className="filetree-container">
        <FileTree></FileTree>
      </div>
    </div>
  );
};

export default App;

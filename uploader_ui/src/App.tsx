import React from "react";
import FileTree from "./components/FileTree";
import "./App.css";
import { RecoilRoot } from "recoil";

const App = () => {
  return (
    <RecoilRoot>
      <div className="app">
        <h1>Uploader UI</h1>
        <div className="filetree-container">
          <FileTree></FileTree>
        </div>
      </div>
    </RecoilRoot>
  );
};

export default App;

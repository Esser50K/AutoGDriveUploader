import React from "react";
import "./App.css";
import { RecoilRoot } from "recoil";
import FileTreePage from "./pages/FileTreePage";

const App = () => {
  return (
    <RecoilRoot>
      <FileTreePage></FileTreePage>
    </RecoilRoot>
  );
};

export default App;

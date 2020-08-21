import React from "react";
import DropDown from "./DropDown"
import { useRecoilState, useSetRecoilState } from "recoil";
import { selectedSyncFolderState, addSyncFolderState, removeSyncFolderState } from "../../states/filetree";
import "./NavBar.css"
import "../../styling/Vars.css"

interface NavBarProps {
    title: string
    syncFolders: string[]
}

const NavBar = (props: NavBarProps) => {
    const [selectedFolder] = useRecoilState(selectedSyncFolderState);
    const addSyncFolder = useSetRecoilState(addSyncFolderState);
    const removeSyncFolder = useSetRecoilState(removeSyncFolderState);
    const splitItem = selectedFolder.split("/");
    const selectedFolderName = splitItem[splitItem.length - 1]

    return (
        <div className="nav-bar">
            <ul className="nav-items">
                <li className="nav-title"><span>{props.title}</span></li>
                <li className="nav-item nav-dropdown">
                    <span className="dropdown-title">
                        {selectedFolder === "" && <div>
                            Currently Selected Folder:
                        </div>}
                        <div className="dropdown-selected">
                            {selectedFolderName || "Configure Sync Folder..."}
                        </div>
                    </span>
                    <DropDown items={props.syncFolders} containerStyle="dropdown-container" itemStyle="dropdown-item"></DropDown>
                </li>
                <li>
                    <div className="sync-folder-actions">
                        <div className="sync-folder-action remove-sync-folder" onClick={() => removeSyncFolder(true)}>
                            Remove Current Sync Folder
                        </div>
                        <div className="sync-folder-action add-sync-folder" onClick={() => addSyncFolder(true)}>
                            Add New Sync Folder
                        </div>
                    </div>
                </li>
            </ul>
        </div >
    )
}

export default NavBar;
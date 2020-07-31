import React, { useEffect } from "react";
import DropDown from "./DropDown"
import { useRecoilState } from "recoil";
import { selectedSyncFolderState } from "../../states/filetree";
import "./NavBar.css"
import "../../styling/Vars.css"

interface NavBarProps {
    title?: string
    syncFolders: string[]
}

const NavBar = (props: NavBarProps) => {
    const [selectedFolder] = useRecoilState(selectedSyncFolderState);

    return (
        <div className="nav-bar">
            <ul className="nav-items">
                {props.title &&
                    <li className="nav-title"><span>{props.title}</span></li>}
                <li className="nav-item nav-dropdown">
                    <span className="dropdown-title">
                        <div>
                            Currently Selected Folder:
                        </div>
                        <div className="dropdown-selected">
                            {props.syncFolders.length > 0
                                ? props.syncFolders[selectedFolder]
                                : "Configure Sync Folder..."}
                        </div>
                    </span>
                    <DropDown items={props.syncFolders} containerStyle="dropdown-container" itemStyle="dropdown-item"></DropDown>
                </li>
            </ul>
        </div >
    )
}

export default NavBar;
import React from "react";
import { useSetRecoilState } from "recoil";
import { selectedSyncFolderState } from "../../states/filetree";

interface DropDownProps {
    items: string[]
    containerStyle: string
    itemStyle: string
}

const DropDown = (props: DropDownProps) => {
    const selectFolder = useSetRecoilState(selectedSyncFolderState);

    return (
        <ul className={props.containerStyle}>
            {props.items.map(
                (name, idx) => (
                    <li key={"dropdown-item" + idx}
                        className={props.itemStyle}
                        onClick={() => selectFolder(idx)}>
                        <span>{name}</span>
                    </li>))}
        </ul>
    )
}

export default DropDown;
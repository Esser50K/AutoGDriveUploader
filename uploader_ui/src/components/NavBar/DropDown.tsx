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
    const syncFolderNames = props.items.map((item) => {
        const splitItem = item.split("/");
        return splitItem[splitItem.length - 1]
    })

    return (
        <ul className={props.containerStyle}>
            {syncFolderNames.map(
                (name, idx) => (
                    <li key={"dropdown-item" + idx}
                        className={props.itemStyle}
                        onClick={() => selectFolder(props.items[idx])}>
                        <span>{name}</span>
                    </li>))}
        </ul>
    )
}

export default DropDown;
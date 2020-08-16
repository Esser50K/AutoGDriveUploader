import React from "react"
import "./ActionButton.css"
import "../../styling/Vars.css"
import { property } from "lodash"

export interface ActionButtonProps {
    text: string
    callback: () => void
}

const ActionButton = (props: ActionButtonProps) => {

    const onClick = (e: React.MouseEvent<HTMLDivElement, MouseEvent>) => {
        e.preventDefault();
        e.stopPropagation();
        props.callback()
    }

    return (
        <div className="abtn-container">
            <div className="abtn-btn" onClick={(e) => onClick(e)}>
                <b>{props.text}</b>
            </div>
        </div>
    )
}

export default ActionButton;
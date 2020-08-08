import React from "react";
import "./ProgressBar.css"
import "../../styling/Vars.css"

interface ProgressBarProps {
    progress: number;
}

const ProgressBar = (props: ProgressBarProps) => {
    return (
        <div className="progress-bar-container">
            <div className="progress-bar-progress" style={{ width: `${(props.progress * 100).toFixed(0)}%` }}>
                <b>{`${(props.progress * 100).toFixed(0)}%`}</b>
            </div>
        </div>
    )
}

export default ProgressBar;
import React, { useState } from "react";
import "./SwitchField.css";
import SwitchPage from "./SwitchPage";

interface SwitchFieldProps {
    switchKey: string;
    networkState: JSON;
}

const SwitchField: React.FC<SwitchFieldProps> = ({ switchKey, networkState }) => {
    const [isSwitchManagementOpen, setSwitchManagementOpen] = useState(false);
    const switchManagement = () => {
        setSwitchManagementOpen(!isSwitchManagementOpen);
    };

    return (
        <div className="switch-container" onClick={switchManagement}>
            <h3 className="header" style={{ color: "white" }}>Switch {switchKey}</h3>
            {isSwitchManagementOpen && <SwitchPage switchKey={switchKey} networkState={networkState} />}
        </div>
    );
};

export default SwitchField;

import React from "react";
import "./SwitchPage.css";
import { LineChart, CartesianGrid, XAxis, YAxis, Tooltip, Legend, Line } from "recharts";
interface SwitchPageProps {
    switchKey: string;
    networkState: JSON;
}

const SwitchPage: React.FC<SwitchPageProps> = ({ switchKey, networkState }) => {


    console.log("SWITCH INFO => ", networkState)

    return (
        <div>
            <h3 className="switchManagementHeader">Switch {switchKey} - Management</h3>
            {/* Additional content for the switch page */}
            <p>Network State: {JSON.stringify(networkState)}</p>
        </div>
    );
};

export default SwitchPage;

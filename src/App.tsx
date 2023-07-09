import React, { useState, useEffect } from 'react';
import './App.css';
import SwitchField from "./components/SwitchField";
import { LineChart, CartesianGrid, XAxis, YAxis, Tooltip, Legend, Line } from "recharts";
import socketIOClient from 'socket.io-client';
import CircularBuffer from './CircularBuffer';

interface NetworkStateWithTimestamp {
  state: any;
  timestamp: string;
}

interface SwitchState {
  [key: string]: number;
}

const App: React.FC = () => {
  const [networkState, setNetworkState] = useState<any>(null);
  const [queue, setQueue] = useState<CircularBuffer<NetworkStateWithTimestamp> | null>(null);
  const [attackerInfo, setAttackerInfo] = useState<any>(null);
  const [meterInfo, setMeterInfo] = useState<any>(null);

  useEffect(() => {
    const socket = socketIOClient("http://127.0.0.1:4001/");

    const circularBuffer = new CircularBuffer<NetworkStateWithTimestamp>(10);
    setQueue(circularBuffer);

    socket.on("message", (networkStateData) => {
      setNetworkState(networkStateData);
      const timestamp = new Date().toISOString(); // Generate a timestamp for the current network state
      const networkStateWithTimestamp: NetworkStateWithTimestamp = { state: networkStateData, timestamp };
      console.log("NETWORK STATE WITH TIMESTAMP => ", networkStateWithTimestamp)

      circularBuffer.enqueue(networkStateWithTimestamp);
    });

    socket.on("attackInfoMessage", (attackData) => {
      setAttackerInfo(attackData);
      console.log("Attacking data => ", attackData)
    });

    socket.on("meterBandsMessage", (meterInfo) => {
      setMeterInfo(meterInfo);
      console.log("Meters data => ", meterInfo)
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  let data: any = [];
  let meterInfoElements = null;


  if (meterInfo) {
    meterInfoElements = Object.keys(meterInfo['Meter bands']).map((switchId) => (
      <p key={switchId}>
        Switch {switchId}: {meterInfo['Meter bands'][switchId]}
      </p>
    ));
  }
  if (queue) {
    // Retrieve the data from the queue and format it for the chart
    data = queue.toArray().map((networkStateWithTimestamp: NetworkStateWithTimestamp) => {
      const timestamp = new Date(networkStateWithTimestamp.timestamp);
      const formattedTimestamp = `${timestamp.getDate()}/${timestamp.getMonth() + 1} - ${timestamp.getHours()}:${timestamp.getMinutes()}:${timestamp.getSeconds()}h`;
      const switchState: SwitchState = {};

      Object.keys(networkStateWithTimestamp.state).forEach((key) => {
        switchState[key] = networkStateWithTimestamp.state[key][11]; // Access the 12th attribute for each switch
      });

      return {
        name: formattedTimestamp,
        ...switchState,
      };
    });
  }

  const switchColors: { [key: string]: string } = {
    "1": "red",
    "2": "blue",
    "3": "yellow",
    "4": "green",
    "5": "pink",
  };

  return (
    <div className='App'>
      <span className='heading'>Cibersegurança com Deep Reinforcement Learning</span>
      <h3 className='header'>Monitorize a sua rede - {networkState && Object.keys(networkState).length} Switches a serem monitorizados</h3>
      <div className='clearfix'>
        {attackerInfo && (
          <div className='attackerInfo'>
            <h4>Current Attacker</h4>
            <p>Attacker ID: {attackerInfo.Attacker}</p>
            <p>Switch Being Attacked: {attackerInfo.Switch}</p>
          </div>
        )}

        {meterInfoElements && (
          <div className='meterInfo'>
            <h4>Meter bands</h4>
            {meterInfoElements}
          </div>
        )}
      </div>
      <div className='graph_packet_count'>
        <LineChart width={1500} height={350} data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" label={{ value: 'Tempo', position: 'insideBottom', dy: 10 }} />
          <YAxis label={{ value: 'Número de pacotes', angle: -90, position: 'insideLeft', dy: -10 }} />
          <Tooltip />
          <Legend formatter={(value) => `Switch ${value}`} />
          {networkState &&
            Object.keys(networkState).map((key) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={switchColors[key]} // Use the defined color for each switch key
                strokeWidth={3}
              />
            ))}
        </LineChart>
      </div>
    </div>
  );
};

export default App;

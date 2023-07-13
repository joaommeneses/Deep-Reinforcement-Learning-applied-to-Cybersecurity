import React, { useState, useEffect } from 'react';
import './App.css';
import { LineChart, CartesianGrid, XAxis, YAxis, Tooltip, Legend, Line } from "recharts";
import socketIOClient from 'socket.io-client';
import CircularBuffer from './CircularBuffer';

interface NetworkStateWithTimestamp {           //Interface que define a estrutura de objetos que guarda o estado da SDN
  state: any;
  timestamp: string;
}

interface SwitchState {                         //Interface que guarda a quantidade de pacotes que passam por cada switch 
  [key: string]: number;
}

const App: React.FC = () => {
  /*
  Variáveis de estado
    networkState: guarda o conteúdo proveniente do ficheiro networkState.json 
    queue: estrutura de dados CircularBuffer, FIFO, que guarda os últimos 10 estados da SDN
    attackerInfo: guarda o conteúdo proviniente do ficheiro attackInfo.json
    meterInfo: guarda o conteúdo proviniente do ficheiro meterBands.json
  */
  const [networkState, setNetworkState] = useState<any>(null);
  const [queue, setQueue] = useState<CircularBuffer<NetworkStateWithTimestamp> | null>(null);
  const [attackerInfo, setAttackerInfo] = useState<any>(null);
  const [meterInfo, setMeterInfo] = useState<any>(null);

  //Hook que lida com o ciclo de vida da aplicação React, é executada antes da página ser renderizada
  useEffect(() => {
    const socket = socketIOClient("http://127.0.0.1:4001/");

    const circularBuffer = new CircularBuffer<NetworkStateWithTimestamp>(10); //Criação do Circular Buffer
    setQueue(circularBuffer);                                                 //Atualização da queue

    socket.on("message", (networkStateData) => {                              //Callback executada quando o servidor de sockets envia uma mensagem com o estado da rede, output guardado em networkStateData
      setNetworkState(networkStateData);                                      //Atualização do estado mais recente da rede
      const timestamp = new Date().toISOString();                             //Gerar nova timestamp
      const networkStateWithTimestamp: NetworkStateWithTimestamp = { state: networkStateData, timestamp };  //Criação de um objeto do tipo NetworkStateWithTimestamp que guarda o estado e a timestamp associada      
      circularBuffer.enqueue(networkStateWithTimestamp);                      //Adicionar estado á queue (primeiro estado inserido na queue é removido quando a queue já guardar 10 estados - FIFO)
    });

    socket.on("attackInfoMessage", (attackData) => {                          //Callback executada quando o servidor de sockets envia uma mensagem com informação relativa ao ataque, output guardado em attackData
      setAttackerInfo(attackData);
    });

    socket.on("meterBandsMessage", (meterInfo) => {                           //Callback executada quando o servidor de sockets envia uma mensagem com informação relativa aos meters da rede, output guardado em meterInfo
      setMeterInfo(meterInfo);
    });

    return () => {
      socket.disconnect();                                                    //Desconectar do socket
    };
  }, []);

  let data: any = [];                                                         //Variável que vai guardar os dados que vão ser apresentados no gráfico
  let meterInfoElements = null;


  if (meterInfo) {
    meterInfoElements = Object.keys(meterInfo['Meter bands']).map((switchId) => (
      <p key={switchId}>
        Switch {switchId}: {meterInfo['Meter bands'][switchId]}
      </p>
    ));
  }
  if (queue) {
    //Atualização dos dados do gráfico 
    data = queue.toArray().map((networkStateWithTimestamp: NetworkStateWithTimestamp) => {
      const timestamp = new Date(networkStateWithTimestamp.timestamp);
      const formattedTimestamp = `${timestamp.getDate()}/${timestamp.getMonth() + 1} - ${timestamp.getHours()}:${timestamp.getMinutes()}:${timestamp.getSeconds()}h`;
      const switchState: SwitchState = {};

      Object.keys(networkStateWithTimestamp.state).forEach((key) => {
        switchState[key] = networkStateWithTimestamp.state[key][11]; // Aceder ao 12º atributo para guardar o número de pacotes que passou pelo switch desde o ultimo estado
      });

      return {
        name: formattedTimestamp,
        ...switchState,
      };
    });
  }

  const switchColors: { [key: string]: string } = {                  //Cores para switches no gráfico
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
                stroke={switchColors[key]}
                strokeWidth={3}
              />
            ))}
        </LineChart>
      </div>
    </div>
  );
};

export default App;

import numpy as np
import tensorflow as tf
import sys
from os import path
import os
import random
from collections import deque

import json

from operator import attrgetter
import simple_switch_13

from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub
from ryu.lib.ip import ipv4_to_bin, ipv4_to_str
from ryu.lib import packet
from ryu.lib.mac import haddr_to_bin

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten
from tensorflow.keras.optimizers import Adam
from keras.layers import Dropout
from tensorflow.keras import layers

from rl.agents import DQNAgent
from rl.policy import BoltzmannQPolicy
from rl.memory import SequentialMemory

from SDNEnvironment import SDNEnvironment


"""
Algorithm DQN Agent Reinforcement Learning

"""

NNEUR = 336  # 4*84 #81 #9
L_H = 1
LAMBD = 0.9  # FOR REWARD
NUMBER_OF_SWITCHES = 5
NUMBER_OF_PORTS_PER_SWITCH = 3  # SWITCH 1 APENAS TEM 2...
MAX_BANDWIDTH = 100
MIN_BANDWIDTH = 0.1 * MAX_BANDWIDTH
SPOOFED_SRC_IP = "10.0.1.1"
DEST_IP = "10.0.0." + str(NUMBER_OF_SWITCHES + 1)

STATE_DIM = 75  # Total de campos por switch (datapath)
ACTION_DIM = 10  # 2 actions para cada switch

MAX_STEP_PER_EP = 100

JSON_PATH = "/media/sf_pasta_partilhada/networkState.json"

class TrafLimit(simple_switch_13.SimpleSwitch13):
    def __init__(self, *args, **kwargs):
        super(TrafLimit, self).__init__(*args, **kwargs)
        self.init_thread = hub.spawn(self._monitor)

        self.datapaths = {}
        self.state = {}
        self.meter_bands = {}
        self.state_prepared = []

        self.attack_count = 0
        self.benign_count = 0
        self.total_attack_count = 0
        self.total_benign_count = 0

    """
    Esta função é chamada quando ocorre uma alteração ao estado da rede como por exemplo um switch é associado ao controlador
    """
    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:  # caso novo switch
            if datapath.id not in self.datapaths:
                self.state[datapath.id] = []
                self.datapaths[datapath.id] = datapath
                self.meter_bands[datapath.id] = MAX_BANDWIDTH
        elif ev.state == DEAD_DISPATCHER:  # switch connection lost
            if datapath.id in self.datapaths:
                del self.datapaths[datapath.id]
                del self.meter_bands[datapath.id]                
        self.state = dict(sorted(self.state.items()))
        self.datapaths = dict(sorted(self.datapaths.items()))

    """
    Função de "inicialização" do controlador
    Espera 5 segundos para dar tempo para iniciar o script de rede do mininet
    Cria o environment no formato correto para o agente (SDNEnvironment)
    Chama função main onde corre o ciclo de treino/teste do agente
    """
    def _monitor(self):
        print("Initializing...")
        hub.sleep(5)
        self.env = SDNEnvironment()
        self.env.controller = self
        self.main()


    """
    Função get_state do controlador
    É chamada pela função reset do SDNEnvironment e após cada ação na função step
    Envia pedido das estatísticas dos flows para os switchs(datapaths)
    Espera 0.5 segundos para as repostas chegarem e serem processadas
    Após o controlador estar atualizado com o estado da rede atual, 
    prepara o estado para o SDNEnvironment (prepare_state_for_model) do agente
    e calcula a reward da ação anterior

    """
    def get_state(self):
        for dp in self.datapaths.values():
            self.send_flow_stats_request(dp)
        hub.sleep(0.5)
        self.prepare_state_for_model()
        self.env.calculate_reward()

    def send_flow_stats_request(self, datapath):
        parser = datapath.ofproto_parser
        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

    """
    Função chamada quando chegam a resposta de um datapath (switch) em relação a um pedido de estatísticas de flow
    """

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        body = ev.msg.body
        datapath = ev.msg.datapath
        ofp_parser = datapath.ofproto_parser

        packet_count_n = 0
        byte_count_n = 0
        duration_nsec = 0

        for stat in [flow for flow in body]:
            packet_count_n += stat.packet_count
            byte_count_n += stat.byte_count
            duration_nsec += stat.duration_nsec
            try: #Se pacotes do flow vierem do host atacante incrementa-se contagem do total de pacotes atacantes na rede
                if (stat.match.__getitem__("ipv4_src") == SPOOFED_SRC_IP and stat.match.__getitem__("ipv4_dst") == DEST_IP and datapath.id in range(2,5)):
                    self.total_attack_count += stat.packet_count
                    if(datapath.id == 4): #Se chegarem ao switch da vítima incrementa-se pacotes de ataque 
                        self.attack_count += stat.packet_count

                elif (stat.match.__getitem__("ipv4_src") != SPOOFED_SRC_IP and datapath.id in range(2,5)) :
                    self.total_benign_count += stat.packet_count #total de pacotes benignos na rede
                    if(datapath.id == 4):
                        self.benign_count += stat.packet_count #total de pacotes benignos que chegam à vitima
            except:
                pass
        #Atualizar estado dos datapaths no controlador
        if len(self.state[datapath.id]) == 0:
            self.state[datapath.id].append({})
            self.state[datapath.id].append(packet_count_n)
            self.state[datapath.id].append(byte_count_n)
            self.state[datapath.id].append(duration_nsec)
        else:
            self.state[datapath.id][1] = packet_count_n
            self.state[datapath.id][2] = byte_count_n
            self.state[datapath.id][3] = duration_nsec
        
        #Pedir estatísticas dos portos dos datapaths
        for port_no in range(1, NUMBER_OF_PORTS_PER_SWITCH + 1):
            req = ofp_parser.OFPPortStatsRequest(datapath, 0, port_no)
            datapath.send_msg(req)

    """
    Função chamada quando chega a respota ao pedido das estatísticas de um porto de um datapath
    """
    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body
        datapath = ev.msg.datapath
        temp = []

        for stat in body:
            temp.append(str(stat.rx_packets))
            temp.append(str(stat.rx_bytes))
            temp.append(str(stat.tx_packets))
            temp.append(str(stat.tx_bytes))
            self.state[datapath.id][0][stat.port_no] = temp
    
    """
    Função usada para executar ação do agente na função step, alterar a meter band de um datapath
    """
    def add_meter_band(self, datapath, rate):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        bands = []
        dropband = parser.OFPMeterBandDrop(rate=int(rate), burst_size=0)
        bands.append(dropband)

        # Apagar meter existente
        request = parser.OFPMeterMod(
            datapath=datapath,
            command=ofproto.OFPMC_DELETE,
            flags=ofproto.OFPMF_PKTPS,
            meter_id=1,
        )
        datapath.send_msg(request)
        # Create novo meter com meter band nova
        request = parser.OFPMeterMod(
            datapath=datapath,
            command=ofproto.OFPMC_ADD,
            flags=ofproto.OFPMF_PKTPS,
            meter_id=1,
            bands=bands,
        )
        datapath.send_msg(request)
        self.send_meter_config_stats_request(datapath)

    """
    As duas funções seguintes pedem a configuração do meter aos switches e processam a respota
    para atualizar o self.meters após uma ação
    """
    def send_meter_config_stats_request(self, datapath):
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        req = ofp_parser.OFPMeterConfigStatsRequest(datapath, 0,
                                                    ofp.OFPM_ALL)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPMeterConfigStatsReply, MAIN_DISPATCHER)
    def meter_config_stats_reply_handler(self, ev):
        body = ev.msg.body
        datapath = ev.msg.datapath
        ofp_parser = datapath.ofproto_parser
        rate = 0
        configs = []
        for stat in body:
            configs.append('length=%d flags=0x%04x meter_id=0x%08x '
                        'bands=%s' %
                        (stat.length, stat.flags, stat.meter_id,
                            stat.bands))
            for band in stat.bands:
                rate = band.rate
        self.meter_bands[datapath.id] = rate
        self.logger.debug('MeterConfigStats: %s', configs)


    """
    Função usada para prepar estado do controlador para o SDNEnvironment do agente
    """
    def prepare_state_for_model(self):
        state_prepared = []

        #Converter o estado em formato de dicionário para lista
        for key in self.state.keys():
            data = self.state[key]
            if data:
                port_data, packet_count, byte_count, duration_nsec = (
                    data[0],
                    data[1],
                    data[2],
                    data[3],
                )

            for port in range(1, 1 + NUMBER_OF_PORTS_PER_SWITCH):
                if port in port_data:
                    for value in port_data[port]:
                        state_prepared.append(value)
                else:
                    for i in range(0, 4):
                        state_prepared.append(0)

            state_prepared.append(packet_count)
            state_prepared.append(byte_count)
            state_prepared.append(duration_nsec)

        # Após converter o estado de dicionário para lista, calculamos a diferença entre o estado novo e o antigo
        if len(state_prepared) != 0:
            #Transformar os valores em inteiros
            state_prepared = list(map(int, state_prepared))

            iter_count = (NUMBER_OF_PORTS_PER_SWITCH * 4 + 3) * NUMBER_OF_SWITCHES

            if(len(self.state_prepared) != 0):
                previous_state = self.state_prepared
            else:
                previous_state = [0]*iter_count

            self.state_prepared = state_prepared

            temp_state = [a - b for a,b in zip(self.state_prepared, previous_state)]


            self.env.state = temp_state #Queremos que o agente DQN treino com as diferenças do estado a cada ação ou seja a cada segundo, 
                                        #para isso definimos o estado do agente como a diferença entre o estado agora e antes da ação há 1 segundo


            ## Escrever estado para ficheiro para aplicação web             
            stateDict = {}

            for i in range(0, len(self.env.state), 15):
                key = str(i // 15 + 1)  # Generating the key as a string
                stateDict[key] = self.env.state[i:i+15]

            print(stateDict)

            json_list = json.dumps(stateDict)

            with open(JSON_PATH, 'w') as json_file:
                json_file.write(json_list)


            print(f"previous_state {previous_state}")
            print(f"prepared state {self.state_prepared}" )
            print(f"temp state {temp_state}" )

    def build_model(self, states, actions):
        model = Sequential()
        model.add(Flatten(input_shape=(1, states)))
        model.add(Dense(NNEUR, activation="relu"))
        for r in range(0, L_H):
            model.add(Dense(NNEUR, activation="relu"))
        model.add(Dense(actions, activation="linear"))
        return model

    def build_agent(self, model, actions):
        policy = BoltzmannQPolicy()
        memory = SequentialMemory(limit=50000, window_length=1)
        dqn = DQNAgent(
            model=model,
            memory=memory,
            policy=policy,
            nb_actions=actions,
            nb_steps_warmup=10 + 40,
            target_model_update=1e-2,
        )
        return dqn

    def main(self):
        print("Starting...")
        model = self.build_model(STATE_DIM, ACTION_DIM)
        dqn = self.build_agent(model, ACTION_DIM)

        dqn.compile(Adam(learning_rate=1e-3), metrics=["mae"])

        num_episodes = 1000
        episode_duration = 10
        monitor_window_size = 1
        steps_per_episode = int(episode_duration / monitor_window_size)
        #steps_per_episode = 10000


        batch_size = 16
        episode = 0
        self.env.reset()
        ### CICLO TESTE ###
        # while True:

        #     print(f"Episode: {episode+1} /{num_episodes}")

        #     # Update the agent
        #     hist = dqn.fit(self.env, nb_steps=steps_per_episode, visualize=False, verbose=1)

        #     #w = np.mean(hist.history['reward'])

        #     if episode+1==num_episodes:
        #         break
        #     episode += 1

        # dqn.save_weights("trained_model.h5", overwrite=True)

        ### CICLO TREINO ###
        while len(self.datapaths) > 0:
            dqn.load_weights("trained_model_5k_episodes.h5")

            dqn.test(self.env, nb_episodes=10, visualize=False, verbose=1)

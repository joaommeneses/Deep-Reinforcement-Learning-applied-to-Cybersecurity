import numpy as np
import tensorflow as tf
from gym import Env
from gym.spaces import Discrete, Box
import random
import math
import time
import datetime
import json


MAX_BANDWIDTH = 100
MIN_BANDWIDTH = 0.1 * MAX_BANDWIDTH
LAMBD = 0.9
NNEUR = 336  # 4*84 #81 #9
L_H = 1
STATE_DIM = 75#45  # Total de campos por switch (datapath)
ACTION_DIM = 10#6  # 2 actions para cada switch
NUMBER_OF_SWITCHES = 5
NUMBER_OF_PORTS_PER_SWITCH = 3


class SDNEnvironment(Env):
    def __init__(self):
        self.action_space = Discrete(ACTION_DIM)
        state_shape = (STATE_DIM,)
        self.observation_space = Box(low=0, high=np.inf, shape=state_shape, dtype=int)
        self.state = []
        self.reward = 0

    """
    Função step do agente, executa ação e calcula reward
    """
    def step(self, action):
        if action % 2 == 0:
            bandwidth = MIN_BANDWIDTH
        else:
            bandwidth = MAX_BANDWIDTH

        if action in [0, 1]:
            dpid = 1
            self.controller.add_meter_band(self.controller.datapaths[dpid], bandwidth)
        elif action in [2, 3]:
            dpid = 2
            self.controller.add_meter_band(self.controller.datapaths[dpid], bandwidth)
        elif action in [4, 5]:
            dpid = 3
            self.controller.add_meter_band(self.controller.datapaths[dpid], bandwidth)
        elif action in [6, 7]:
            dpid = 4
            self.controller.add_meter_band(self.controller.datapaths[dpid], bandwidth)
        elif action in [8, 9]:
            dpid = 5
            self.controller.add_meter_band(self.controller.datapaths[dpid], bandwidth)

        previous_state = self.state
        self.controller.get_state()
        time.sleep(0.5) # Este 0.5 segundos mais 0.5 segundos no get_state ~= 1 segundo entre cada ação

        reward = self.reward
        done = False

        self.controller.attack_count = 0
        self.controller.benign_count = 0
        self.controller.total_attack_count = 0
        self.controller.total_benign_count = 0

        return previous_state, reward, done, {}

    def calculate_reward(self):
        global pa, pb

        print("\ntotal packets attack " + str(self.controller.total_attack_count) + " attack_count " + str(self.controller.attack_count))
        print("total packets benign " + str(self.controller.total_benign_count) + " benign_count " + str(self.controller.benign_count))
        print("Meter bands " + str(self.controller.meter_bands))
        #MAX LOAD = (MAX_BANDWIDTH PACKETS/S * PORTS OF SWITCH) * 5 
        #max_load = (MAX_BANDWIDTH * NUMBER_OF_PORTS_PER_SWITCH) * 4 + (MAX_BANDWIDTH*2) #PS: Switch 1 only has 2 ports


        # if((self.controller.total_attack_count + self.controller.total_benign_count) > max_load):
        #     self.reward = -1
        # else:
        #     if(self.controller.total_attack_count == 0):
        #         pa = 0
        #     else:
        #         pa = float(self.controller.attack_count) / float(self.controller.total_attack_count)

        #     if(self.controller.total_benign_count == 0):
        #         pb = 0
        #     else:
        #         pb = float(self.controller.benign_count) / float(self.controller.total_benign_count)

        #     self.reward = float(LAMBD * pb) + float((1 - LAMBD) * (1 - pa))

        # 2λpb + 2(1 − λ)(1 − pa) - 1
        if(self.controller.total_attack_count == 0 and self.controller.total_benign_count==0):
            self.reward = 0.0            
        else:            
            if(self.controller.total_attack_count == 0):
                pa = 0
            else:
                pa = float(self.controller.attack_count) / float(self.controller.total_attack_count)

            if(self.controller.total_benign_count == 0):
                pb = 0
            else:
                pb = float(self.controller.benign_count) / float(self.controller.total_benign_count)

            self.reward = float(2*LAMBD * pb) + float(2*(1 - LAMBD) * (1 - pa)) - float(1)            
            

        print("Saving meter bands...")
        with open("meterBands.json", "w") as file:
            json.dump({"Meter bands": self.controller.meter_bands}, file)
                                   

    def render(self):
        pass

    def reset(self):
        for i in range(1, NUMBER_OF_SWITCHES + 1):
            self.controller.add_meter_band(self.controller.datapaths[i], MAX_BANDWIDTH)
            pass
        self.controller.get_state()
        return self.state

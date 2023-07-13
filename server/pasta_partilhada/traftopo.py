from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import OVSSwitch, Switch, Controller, RemoteController
import random
import threading
import json


JSON_PATH = "/media/sf_pasta_partilhada/attackInfo.json"

class TrafTopo(Topo):
    def build(self):
        # Open flow switches
        s1 = self.addSwitch('s1', cls=OVSSwitch)
        s2 = self.addSwitch('s2', cls=OVSSwitch)
        s3 = self.addSwitch('s3', cls=OVSSwitch)
        s4 = self.addSwitch('s4', cls=OVSSwitch)
        s5 = self.addSwitch('s5', cls=OVSSwitch)

        #Hosts
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')
        h5 = self.addHost('h5')
        h6 = self.addHost('h6')

        #links switches
        self.addLink(s1,s5)
        self.addLink(s2,s1)
        self.addLink(s3,s5)
        self.addLink(s4,s5)

        #links hosts - switches
        self.addLink(s2,h1)
        self.addLink(s2,h2)
        self.addLink(s3,h3)
        self.addLink(s3,h4)
        self.addLink(s4,h5)
        self.addLink(s4,h6)

if __name__ == '__main__':
    topo = TrafTopo()
    controllerRyu = RemoteController('controllerRyu','10.0.2.15', 6653) #IP e PORTO do controlador RYU
    net = Mininet(topo=topo, controller=controllerRyu, autoSetMacs=True, waitConnected=True) #waitConnected faz com que a rede apenas começe quando um controlador estiver conectado

    #start network
    net.start()

    
    # simular ataque DDoS e tráfego benigno

    episode_count = 10000
    episode_length = 10
    no_of_hosts = 6
    victim_host_ip = '10.0.0.' + str(no_of_hosts)
    spoofed_ip = '10.0.1.1'

    #-i u10000 (10 packets for second)
    #-i u1000 (100 packets for second)

    #ddos
    def ddos_flood_tcp(host):
        host.cmd('timeout ' + str(episode_length) + 's hping3 -i u1000 ' + ' -a '+ spoofed_ip +' '+ victim_host_ip)
        host.cmd('killall hping3')

    def ddos_flood_udp(host):
        host.cmd('timeout ' + str(episode_length) + 's hping3 -i u1000 --udp ' + ' -a '+ spoofed_ip +' '+ victim_host_ip)
        host.cmd('killall hping3')


    def ddos_flood_icmp(host):
        host.cmd('timeout ' + str(episode_length) + 's hping3 -i u1000 --icmp ' + ' -a '+ spoofed_ip +' '+ victim_host_ip)
        host.cmd('killall hping3')

    #benign
    def ddos_benign(host):
        host.cmd('timeout ' + str(episode_length) + 's hping3 ' + victim_host_ip)
        host.cmd('killall hping3')

    # host atacante e host benigno random
    for i in range(episode_count):
        print("Episode "+str(i))
        attacking_host_id = random.randint(0, no_of_hosts - 2) # host atacante random entre 1 e no_of_hosts - 1
        attacking_host = net.hosts[attacking_host_id]

        benign_host_id = random.choice([i for i in range(0, no_of_hosts - 2) if i not in [attacking_host_id]]) # host benigno random entre 1 e no_of_hosts - 2
        benign_host = net.hosts[benign_host_id]
        print("host" + str(attacking_host_id) + " is attacking and host" + str(benign_host_id) + " is sending normal requests")

        # threads separadas para attacking host e benign host
        t1 = threading.Thread(target=ddos_benign, args=(benign_host,))

        #t2 = threading.Thread(target=ddos_flood_tcp, args=(attacking_host,)) 
        if(i<=3500):
            t2 = threading.Thread(target=ddos_flood_tcp, args=(attacking_host,)) 
        elif(i<=7000):
            t2 = threading.Thread(target=ddos_flood_udp, args=(attacking_host,))
        elif(i<=10000):
            t2 = threading.Thread(target=ddos_flood_icmp, args=(attacking_host,))

        
        # switch a ser atacado
        if attacking_host_id in [0, 1]:
            switch_id = 2
        elif attacking_host_id in [2, 3]:
            switch_id = 3
        elif attacking_host_id in [4, 5]:
            switch_id = 4

        # dicionario com informação de ataque para aplicação web
        attack_info = {"Attacker": str(attacking_host_id), "Switch": str(switch_id)}
        attack_info_list = json.dumps(attack_info)
        # Guardar informação do ataque num ficheiro json
        with open(JSON_PATH, 'w') as file:
            file.write(attack_info_list)

        t1.start()
        t2.start()                

        t1.join()
        t2.join()


    #stop network    
    net.stop()

topos = { 'trafTopo': ( lambda: TrafTopo() ) }

from mininet.net import Mininet
from mininet.topolib import TreeTopo
from mininet.node import Controller, RemoteController,OVSSwitch

import random
import threading

# Create and start mininet topology
tree_topo = TreeTopo(depth=2, fanout=2)
controllerRyu = RemoteController('controllerRyu','10.0.2.15', 6653)
net = Mininet(topo=tree_topo, controller=controllerRyu,switch=OVSSwitch, waitConnected=True)
net.start()

episode_count = 10000
episode_length = 10
no_of_hosts = 4
victim_host_ip = '10.0.0.' + str(no_of_hosts)
spoofed_ip = '10.0.1.1'

# Command line tool hping3 is used to simulate DDoS
def ddos_flood_tcp(host):
    #ddos
    host.cmd('timeout ' + str(episode_length) + 's hping3 -i u1000 ' + ' -a '+ spoofed_ip +' '+ victim_host_ip)
    host.cmd('killall hping3')

def ddos_flood_udp(host):
    host.cmd('timeout ' + str(episode_length) + 's hping3 -i u1000 --udp ' + ' -a '+ spoofed_ip +' '+ victim_host_ip)
    host.cmd('killall hping3')


def ddos_flood_icmp(host):
    host.cmd('timeout ' + str(episode_length) + 's hping3 -i u1000 --icmp ' + ' -a '+ spoofed_ip +' '+ victim_host_ip)
    host.cmd('killall hping3')

def ddos_benign(host):
    #benign
    host.cmd('timeout ' + str(episode_length) + 's hping3 ' + victim_host_ip)
    host.cmd('killall hping3')


# In each episode Randomly select attacker and bengin user 
for i in range(episode_count):
    print("Episode "+str(i))
    attacking_host_id = random.randint(0, no_of_hosts - 2) # select a random host in between 1 and no_of_hosts - 1
    attacking_host = net.hosts[attacking_host_id]

    benign_host_id = random.choice([i for i in range(0, no_of_hosts - 2) if i not in [attacking_host_id]])
    benign_host = net.hosts[benign_host_id]
    print("host" + str(attacking_host_id) + " is attacking and host" + str(benign_host_id) + " is sending normal requests")

    # Create seperate threads for attacker and benign user
    t1 = threading.Thread(target=ddos_benign, args=(benign_host,))
    t2 = threading.Thread(target=ddos_flood_tcp, args=(attacking_host,)) 
 
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()


net.stop()
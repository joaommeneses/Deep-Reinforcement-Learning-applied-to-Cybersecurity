# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ipv4
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types

MAX_BANDWIDTH=100

class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION] #OpenFlow Version 1.3

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}


    '''
    Esta função é chamada quando um evento do tipo EventOFPSwitchFeatures ocorre através do 
    dispatcher CONFIG na redem
    ou seja, é chamada quando o switch responde ao controlador com as suas caracteristicas 
    durante o handshake inicial entre switch e controlador
    ''' 
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        #Criar match vazio para flow entry "TABLE_MISS" do switch
        match = parser.OFPMatch()
        #Actions = mandar pacote para o controlador sem fazer buffering
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        
        self.add_flow(datapath, 0, match, actions, meter=None)

        #Adicionar meter ao switch com limite de tráfego máximo
        bands = []
        dropband = parser.OFPMeterBandDrop(rate=MAX_BANDWIDTH, burst_size=0)
        bands.append(dropband)
        #Request para adicionar meter ao switch
        request = parser.OFPMeterMod(datapath=datapath,
                                        command=ofproto.OFPMC_ADD,
                                        flags=ofproto.OFPMF_PKTPS,
                                        meter_id=1,
                                        bands=bands)
        #Enviar request ao switch
        datapath.send_msg(request)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None, meter= None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        #Se meter != None adicionar meter ID(1) ao flow para além das ações
        if meter:
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions),parser.OFPInstructionMeter(1)]
        else:
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        
        #Se for um pacote buffered é o id do buffer é adicionado à mensagem de criação de flow entry
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    '''
    Função é chamada caso chegue um pacote ao controlador através do flow "TABLE_MISS"
    '''
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return

        #mac addresses
        dst = eth.dst
        src = eth.src

        #ipv4
        ip = pkt.get_protocol(ipv4.ipv4)
        dst_ip = ""
        src_ip = ""     

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        #self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        #Se pacote tiver um destino conhecido não é feito FLOOD
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # Criar flow para não ocorrer "TABLE_MISS" da próxima vez
        if out_port != ofproto.OFPP_FLOOD:
            if (ip):
                dst_ip = ip.dst
                src_ip = ip.src
                match = parser.OFPMatch(in_port=in_port, eth_dst=dst,eth_src=src, eth_type = 0x0800, ipv4_dst = dst_ip, ipv4_src = src_ip)
            else:
                match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            # verify if we have a valid buffer_id, if yes avoid to send both
            #Instalar flow novo
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id, meter=True)
                return
            else:
                self.add_flow(datapath, 1, match, actions, meter=True)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        #Enviar pacote de volta
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)


        

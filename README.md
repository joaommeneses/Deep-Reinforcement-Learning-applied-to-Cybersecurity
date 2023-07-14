# Cibersegurança com Deep Reinforcement Learning

Este projeto consiste na mitigação de ataques DDoS numa rede definida por software simulada com Mininet e Ryu. Para a mitigação é usado um agente DQN.
É também usado uma aplicação web em react para monitorizar a rede.

## Como correr o projeto

Aplicação web  e servidor de sockets (Pode ser na máquina host Windows):

Para a aplicação web:
### `npm install` caso seja a primeira vez (instala node_modules com os modulos necessários)
### `npm start`

Para correr servidor de sockets:

### `node index.js`

## Localização dos ficheiros relacionadas à SDN (rede definida por software) e ao Agente

Os ficheiros relacionados à SDN e ao agente encontram-se no caminho ./server/pasta_partilhada que corresponde a uma pasta partilha com a máquina virtual
O servidor de sockets necessita que a localização dos ficheiros esteja no caminho ./server/pasta_partilhada

# Agente e SDN

Para correr a SDN e o Agente de mitigação (numa máquina virtual linux e.g: ubuntu):

Correr controlador Ryu
### `ryu-manager traflimit.py`
Começar rede simulada no Mininet
### `python3.9 traftopo.py`



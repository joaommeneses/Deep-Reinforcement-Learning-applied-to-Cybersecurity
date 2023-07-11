# Cibersegurança com Deep Reinforcement Learning

Este projeto consiste na mitigação de ataques DDoS numa rede definida por software simulada com Mininet e Ryu. Para a mitigação é usado um agente DQN.
É também usado uma aplicação web em react para monitorizar a rede.

## Como correr o projeto

Para correr a SDN e o Agente de mitigação:

Correr controlador Ryu
### ryu-manager traflimit.py
Começar rede simulada no Mininet
### python3.9 traftopo.py

Aplicação web  e servidor de sockets:

Para a aplicação web:
### `npm start`

Para correr servidor de sockets:

### node index.js

## Localização dos ficheiros relacionadas à SDN (rede definida por software) e ao Agente

Os ficheiros relacionados à SDN e ao agente encontram-se no caminho ./server/pasta_partilhada

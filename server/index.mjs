import express from 'express';
import http from 'http';
import * as socketio from 'socket.io';
import fs from 'fs';

const port = 4001;
const app = express();
const httpServer = http.createServer(app);
const server = new socketio.Server(httpServer, {
    cors: {
        origin: '*',
    },
});

let lastModifiedTime = null;
let lastAttackData = null;
let lastMeterBands = null;

server.on('connection', (socket) => {
    console.log('Connected');

    // Ver se ficheiro networkState.json sofreu alterações
    fs.watch('pasta_partilhada/networkState.json', (eventType, filename) => {
        if (eventType === 'change' && filename === 'networkState.json') {
            // Ficheiro foi modificado            
            fs.stat('pasta_partilhada/networkState.json', (err, stats) => {
                if (err) {
                    console.error('Error reading networkState.json:', err);
                    return;
                }

                const currentModifiedTime = stats.mtimeMs;

                if (lastModifiedTime === null || currentModifiedTime > lastModifiedTime) {
                    // Ler conteúdo do ficheiro networkState.json
                    fs.readFile('pasta_partilhada/networkState.json', 'utf8', (err, data) => {
                        if (err) {
                            console.error('Error reading networkState.json:', err);
                            return;
                        }

                        // Fazer parse dos dados para JSON
                        let networkStateData = null;
                        try {
                            networkStateData = JSON.parse(data);
                        } catch (error) {
                            console.error('Error parsing networkState.json:', error);
                            return;
                        }

                        // mandar dados para o socket cliente conectado
                        socket.emit('message', networkStateData);

                        // Atualizar a ultima atualização
                        lastModifiedTime = currentModifiedTime;
                    });
                }
            });
        }
    });



    // Ver se ficheiro attackInfo.json sofreu alterações
    fs.watch('pasta_partilhada/attackInfo.json', (eventType, filename) => {
        if (eventType === 'change' && filename === 'attackInfo.json') {
            // Ficheiro foi modificado                
            fs.stat('pasta_partilhada/attackInfo.json', (err, stats) => {
                if (err) {
                    console.error('Error reading attackInfo.json:', err);
                    return;
                }

                const currentModifiedTime = stats.mtimeMs;

                // Ler conteúdo do ficheiro attackInfo.json
                fs.readFile('pasta_partilhada/attackInfo.json', 'utf8', (err, data) => {
                    if (err) {
                        console.error('Error reading attackInfo.json:', err);
                        return;
                    }

                    // Fazer parse dos dados para JSON
                    let attackData = null;
                    try {
                        attackData = JSON.parse(data);
                    } catch (error) {
                        console.error('Error parsing attackInfo.json:', error);
                        return;
                    }

                    // Comparar dados lidos com os ultimos dados lidos
                    //se não existirem dados lidos guardar dados atuais
                    if (lastAttackData == null) {
                        lastAttackData = attackData
                        socket.emit('attackInfoMessage', attackData);
                    }
                    //se existirem dados, verificar se existe diferença de conteúdo
                    else if (JSON.stringify(attackData) !== JSON.stringify(lastAttackData)) {
                        //Dados são diferentes                             
                        //Enviar dados para socket cliente conectado
                        socket.emit('attackInfoMessage', attackData);


                        //atualizar dados antigos para dados atuais e data de ultima alteração
                        lastModifiedTime = currentModifiedTime;
                        lastAttackData = attackData;
                    }
                });
            });
        }
    });

    // Ver se ficheiro meterBands.json sofreu alterações
    fs.watch('pasta_partilhada/meterBands.json', (eventType, filename) => {
        if (eventType === 'change' && filename === 'meterBands.json') {
            // Ficheiro foi modificado     
            fs.stat('pasta_partilhada/meterBands.json', (err, stats) => {
                if (err) {
                    console.error('Error reading meterBands.json:', err);
                    return;
                }

                const currentModifiedTime = stats.mtimeMs;

                // Ler conteúdo do ficheiro meterBands.json
                fs.readFile('pasta_partilhada/meterBands.json', 'utf8', (err, data) => {
                    if (err) {
                        console.error('Error reading meterBands.json:', err);
                        return;
                    }

                    // Fazer parse dos dados para JSON
                    let meterBands = null;
                    try {
                        meterBands = JSON.parse(data);
                    } catch (error) {
                        console.error('Error parsing meterBands.json:', error);
                        return;
                    }

                    // Comparar dados lidos com os ultimos dados lidos
                    //se não existirem dados lidos guardar dados atuais
                    if (lastMeterBands == null) {
                        lastMeterBands = meterBands
                        socket.emit('meterBandsMessage', meterBands);
                    }
                    //se existirem dados, verificar se existe diferença de conteúdo
                    else if (JSON.stringify(meterBands) !== JSON.stringify(lastMeterBands)) {
                        //Dados são diferentes                             
                        //Enviar dados para socket cliente conectado
                        socket.emit('meterBandsMessage', meterBands);

                        //atualizar dados antigos para dados atuais e data de ultima alteração
                        lastModifiedTime = currentModifiedTime;
                        lastMeterBands = meterBands;
                    }
                });
            });
        }
    });
});

//Conectar a porto
httpServer.listen(port, () => {
    console.log(`Socket server listening on port ${port}`);
});

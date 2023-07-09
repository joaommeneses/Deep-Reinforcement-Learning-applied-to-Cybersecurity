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

    // Watch the networkState.json file for changes
    fs.watch('pasta_partilhada/networkState.json', (eventType, filename) => {
        if (eventType === 'change' && filename === 'networkState.json') {
            // File has been modified
            console.log('networkState.json updated');

            fs.stat('pasta_partilhada/networkState.json', (err, stats) => {
                if (err) {
                    console.error('Error reading networkState.json:', err);
                    return;
                }

                const currentModifiedTime = stats.mtimeMs;

                if (lastModifiedTime === null || currentModifiedTime > lastModifiedTime) {
                    // Read the contents of the networkState.json file
                    fs.readFile('pasta_partilhada/networkState.json', 'utf8', (err, data) => {
                        if (err) {
                            console.error('Error reading networkState.json:', err);
                            return;
                        }

                        // Parse the JSON data
                        let networkStateData = null;
                        try {
                            networkStateData = JSON.parse(data);
                        } catch (error) {
                            console.error('Error parsing networkState.json:', error);
                            return;
                        }

                        // Send the data to the connected socket client
                        socket.emit('message', networkStateData);

                        // Update the last modified time
                        lastModifiedTime = currentModifiedTime;
                    });
                }
            });
        }
    });



    // Watch the attackInfo.json file for changes
    fs.watch('pasta_partilhada/attackInfo.json', (eventType, filename) => {
        if (eventType === 'change' && filename === 'attackInfo.json') {
            // File has been modified
            console.log('attackInfo.json updated');

            fs.stat('pasta_partilhada/attackInfo.json', (err, stats) => {
                if (err) {
                    console.error('Error reading attackInfo.json:', err);
                    return;
                }

                const currentModifiedTime = stats.mtimeMs;

                // Read the contents of the attackInfo.json file
                fs.readFile('pasta_partilhada/attackInfo.json', 'utf8', (err, data) => {
                    if (err) {
                        console.error('Error reading attackInfo.json:', err);
                        return;
                    }

                    // Parse the JSON data
                    let attackData = null;
                    try {
                        attackData = JSON.parse(data);
                    } catch (error) {
                        console.error('Error parsing attackInfo.json:', error);
                        return;
                    }

                    // Compare the data with the previous content
                    if (lastAttackData == null) {
                        lastAttackData = attackData
                    }
                    if (JSON.stringify(attackData) !== JSON.stringify(lastAttackData)) {
                        // Data has changed
                        console.log('attackInfo.json data has changed');

                        // Send the data to the connected socket client
                        socket.emit('attackInfoMessage', attackData);

                        // Update the last modified time and data
                        lastModifiedTime = currentModifiedTime;
                        lastAttackData = attackData;
                    }
                });
            });
        }
    });

    // Watch the meterBands.json file for changes
    fs.watch('pasta_partilhada/meterBands.json', (eventType, filename) => {
        if (eventType === 'change' && filename === 'meterBands.json') {
            // File has been modified
            console.log('meterBands.json updated');

            fs.stat('pasta_partilhada/meterBands.json', (err, stats) => {
                if (err) {
                    console.error('Error reading meterBands.json:', err);
                    return;
                }

                const currentModifiedTime = stats.mtimeMs;

                // Read the contents of the meterBands.json file
                fs.readFile('pasta_partilhada/meterBands.json', 'utf8', (err, data) => {
                    if (err) {
                        console.error('Error reading meterBands.json:', err);
                        return;
                    }

                    // Parse the JSON data
                    let meterBands = null;
                    try {
                        meterBands = JSON.parse(data);
                    } catch (error) {
                        console.error('Error parsing meterBands.json:', error);
                        return;
                    }

                    if (lastMeterBands == null) {
                        lastMeterBands = meterBands
                    }
                    // Compare the data with the previous content
                    if (JSON.stringify(meterBands) !== JSON.stringify(lastMeterBands)) {
                        // Data has changed
                        console.log('meterBands.json data has changed');

                        // Send the data to the connected socket client
                        socket.emit('meterBandsMessage', meterBands);

                        // Update the last modified time and data
                        lastModifiedTime = currentModifiedTime;
                        lastMeterBands = meterBands;
                    }
                });
            });
        }
    });
});

httpServer.listen(port, () => {
    console.log(`Socket server listening on port ${port}`);
});


let websocket = (function() {
    let socket = null;
    let requests = {};

    let generateRequestId = () => {
        let token = randomBigInt(requestTokenLength).toString(16);
        while(token in requests) { 
            // don't sent the same request token twice while it has not been responded to
            token = randomBigInt(requestTokenLength).toString(16);   
        }
        return token;
    }


    return {
        init: function(url) {
            // establish websocket connection
            // authenticate for channels
            // add handler for incoming data
            socket = new WebSocket(url);
            socket.onopen = function() {
                debug("connected");
                authenticate();
            };
            socket.onmessage = function(event) {
                let message = JSON.parse(event.data);
                debug("received message", message);
                if(message["subject"] == "acknowledge") {
                    let request = requests[message["responseTo"]];
                    request.acknowledged = true;
                } else if(message["subject"] == "response") {
                    let request = requests[message["responseTo"]].data;
                    delete requests[message["responseTo"]];

                    debug(request);
                    if(
                        request.behavior != null 
                        && request.behavior.callback != null
                    ) {
                        request.behavior.callback(message, request);
                    }
                } else {
                    // unknown message - maybe wrong version?
                }
            };
        },
        send: function(subject, message, acknowledge=false) {
            // add request token
            // store information on what to do with the response
            // store information on what to do with no response
            // send minified data
            message.header: {
                subject: subject
                , acknowledge: acknowledge
            };
            if(acknowledge == true) {
                message.header.id = generateRequestId();
                requests[message.header.id] = message;

                message = JSON.parse(JSON.stringify(message));
                delete message.behavior; // not needed information should only be stored on device
            }

            socket.send(JSON.stringify(message));
            debug("sending message", message);
        },
    };
})();

// server-side database operation integration
function sendMessage(from, to, message, callback) {
    websocket.send("send message", {
        id: from
        , to: to
        , message: message
        , behavior: {
            method: function(serverData, clientData) {
            },
        }
    }, true);
}

// server-side database operation integration
function authenticate(entities) {
    if(entities == null) {
        // authenticate all active entities
        entities = database.messenger.personas.get({
            field: 'active', values: true
        }).reduce(function(all, persona) {
            return all.concat(persona.connections.filter(function(conn) {
                return conn.active == true
            }))
        }, []);
    }

    entities = entities.map(function(entity) { 
        return {
            id: entity.id
            , password: entity.password
            , parent: entity.parent == null ? null : {
                id: entity.parent.id,
                password: entity.parent.password
            }
        };
    });

    if(entities.length > 0) {
        websocket.send("authenticate", {
            entities: entities
        }, true);
    }
}

//
function createPersona() {

}

// server-side database operation integration
function requestChannels(success, parents) {
    if(Array.isArray(parents) == false) {
        parents = [parents];
    }
    if(parents.length == 0) {
        // nothing to do
        return;
    }

    websocket.send("create entities", {
        entities: parents.map(function(parent) {
            password: generateSecret().toString(16),
            parent: parent == null ? null : {
                id: parent.id,
                password: parent.password
            }
        }), behavior: {
            callback: function(serverData, clientData) {
                if(serverData["status"] == "success") {
                    if(serverData.ids.length == clientdata.entities.length) {
                        error("entities and ids do not match in number, abort ..");
                        return;
                    }

                    let parentIds = new Set();
                    for(let entity of clientData.entities) {
                        if(entity.parent != null) {
                            parentIds.push(entity.parent.id);
                        }
                    }

                    database.messenger.accounts.get({
                        values:parentIds
                    });

                    let newEntities = [];
                    for(let i = 0; i < serverData.ids.length; ++i) {
                        entity = clientData.entities[i];
                        let created = {
                            id: serverData.ids[i],
                            password: clientData.entities[i].password,
                            active: true,
                        }

                        if(entity.parent != null) {
                            account = database.messenger.accounts.get(
                                entity.parent.id
                            );
                            created.parent = account;
                            account.connections.push(created)
                            database.messenger.accounts.save(account);
                        } else {
                            database.messenger.accounts.save(created);
                        }
                        newEntities.push(created); 
                    }

                    authenticate(newEntities);

                    info("new entities: ", newEntities);
                    if(success) {
                        success(newEntities);
                    }
                } else {
                    error("create account request failed");
                    if(error) {
                        error()
                    }
                }
            }
        }
    }, true);
}
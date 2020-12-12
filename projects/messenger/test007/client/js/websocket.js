
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
                authenticate(database.messenger.accounts.get({
                    field:'active', values:true
                }));
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
            message = {
                subject: subject
                , acknowledge: acknowledge
                , data: message
            };
            if(acknowledge == true) {
                message.id = generateRequestId();
                requests[message.id] = message;

                message = JSON.parse(JSON.stringify(message));
                delete message.data['behavior']; // not needed information should be stored in handling
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
function authenticate(channels) {
    channels = channels.map(function(channel) { 
        return {
            id: channel.id
            , password: channel.password
        }
    });

    if(channels.length > 0) {
        websocket.send("authenticate", {
            channels: channels
        }, true);
    }
}

// server-side database operation integration
function requestChannel(callback) {
    let password = generateSecret().toString(16);

    websocket.send("create channel", {
        password: password
        , behavior: {
            callback: function(serverData, clientData) {
                if(serverData["status"] == "success") {
                    let account = {
                        id: serverData.id,
                        password: clientData.password,
                        active: true,
                    };

                    database.messenger.accounts.save(account);
                    authenticate([account]);

                    info("new account: ", account);
                    if(callback) {
                        callback(account);
                    }
                } else {
                    error("create account request failed");
                }
            }
        }
    }, true);
}
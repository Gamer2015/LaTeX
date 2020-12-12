let websocket = (function() {
    let socket = null;
    let requests = {};

    let generateRequestToken = () => {
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
            };
            socket.onmessage = function(e) {
                let data = JSON.parse(e.data);
                debug("received message", data);
                if(data["message"] == "response") {
                    let request = requests[data["responseTo"]];
                    delete requests[request.requestToken];

                    request.callback.method(data, request);
                } else if(data["message"] == "new message") {

                }
            };
        },
        send: function(request) {
            // add request token
            // store callback information
            // send minified data
            request.requestId = generateRequestToken();
            requests[request.requestId] = request;

            minified = Object.assign({}, request);
            delete minified['callback']; // not needed information should be stored in callback

            socket.send(JSON.stringify(minified));
            debug("sending request", minified);
        },
    };
})()

// server-side database operation integration
function sendMessage(from, to, message, callback) {
    websocket.send({
        message: "send message"
        , id: fromId
        , password: password
        , to: to
        , message: message
        , callback: {
            method: function(serverData, clientData) {
            },
        }
    });
}

// server-side database operation integration
function authenticate(channels, callback) {
    websocket.send({
        message: "authenticate",
        channels: channels,
        callback: {
            method: function(serverData, clientData) {
            },
        }
    });
}

// server-side database operation integration
function requestChannel(callback) {
    let password = generateSecret().toString(16);

    websocket.send({
        message: "create channel",
        password: password,
        callback: {
            method: function(serverData, clientData) {
                if(serverData["status"] == "success") {
                    let channel = {
                        id: serverData.id,
                        password: clientData.password,
                    };

                    database.messenger.passwords.save(channel);

                    info("new channel: ", channel);
                    if(callback) {
                        callback(channel);
                    }
                } else {
                    error("create channel request failed");
                }
            },
        }
    });
}
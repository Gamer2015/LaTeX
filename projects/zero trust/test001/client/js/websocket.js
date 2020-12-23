
let websocket = (function() {
    let socket = null;
    let messages = {};

    let generateRequestId = () => {
        let token = generateMessageIds()[0];
        while(token in messages) { 
            // don't sent the same request token twice while it has not been responded to
            token = generateMessageIds()[0];
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
                let subject = message["header"]["subject"]
                if(subject == "response") {
                    let requestId = message["responseTo"];
                    let request = messages[requestId];
                    delete messages[requestId];

                    debug(request);
                    if(
                        request.behavior != null 
                        && request.behavior.callback != null
                    ) {
                        request.behavior.callback(message, request);
                    }
                } else {
                    // unknown message - maybe wrong version? 
                    // oh oh ... version support ...
                }
            };
        },
        send: function(subject, message) {
            // add request token
            // store information on what to do with the response
            // store information on what to do with no response
            // send minified data
            message.header = {
                subject: subject
            };
            if('behavior' in message) {
                // expect a response to this message
                message.header.id = generateRequestId();
                messages[message.header.id] = message;

                message = JSON.parse(JSON.stringify(message));  
                delete message.behavior; // not needed information should be stored on device
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
    });
}

// server-side database operation integration
function authenticate(accounts) {
    if(accounts == null) {
        // authenticate all active accounts
        accounts = [];

        request = window.indexedDB.open('database')
        request.onsuccess = function(event) {
            let db = request.result;
            let transaction = db.transaction('accounts');
            transaction.oncomplete = function(event) {
                if(accounts.length != 0) {
                    authenticate(accounts);
                }
            };

            let index = transaction.objectStore('accounts').index('active');
            index.openCursor(IDBKeyRange.only('true')).onsuccess = function(event) {
                let cursor = event.target.result;
                if(cursor) {
                    accounts.push(cursor.value);
                    cursor.continue();
                }
            }   
        }
        return; 
    }

    if(Array.isArray(accounts) == false) {
        accounts = [accounts]
    }
    if(accounts.length == 0) {
        return;
    }

    accounts = accounts.map(function(account) { 
        return {
            id: account.id
            , password: account.password
        };
    });

    websocket.send("authenticate", {
        accounts: accounts
        , behavior: {
            callback: function(serverData, clientData) {
                if(serverData["status"] == "success") {
                    info("authentication successful", accounts);
                } else {
                    error("authentication request failed", accounts);
                    if(error) {
                        error()
                    }
                }
            }
        }
    });
}

// server-side database operation integration
function requestAccounts(success, error, number=1) {
    let secrets = generateSecrets(number);
    let passwords = calculatePasswords(secrets);

    // sjcl.decrypt("password", "encrypted-data")

    websocket.send("create accounts", {
        accounts: secrets.map(function(secret) { return {
            password: calculatePassword(secret)
        }}), behavior: {
            secrets: secrets
            , callback: function(serverData, clientData) {
                if(serverData["status"] == "success") {
                    let secrets = clientData.behavior.secrets;
                    if(serverData.ids.length != secrets.length) {
                        error("accounts and ids do not match in number, abort ...");
                        return;
                    }

                    let createdAccounts = [];
                    for(let i = 0; i < serverData.ids.length; ++i) {
                        createdAccounts.push({
                            id: serverData.ids[i],
                            secret: secrets[i],
                            password: clientData.accounts[i].password,
                            active: 'true',
                        });
                    }

                    request = window.indexedDB.open('database')
                    request.onsuccess = function(event) {
                        let db = request.result;
                        let transaction = db.transaction(['accounts'], 'readwrite');
                        transaction.oncomplete = function(event) {
                            if(success) {
                                success(createdAccounts);
                            }
                        };

                        let store = transaction.objectStore('accounts');
                        for(let account of createdAccounts) {
                            store.put(account);
                        }
                    }

                    info("new accounts: ", createdAccounts);
                    authenticate(createdAccounts);
                } else {
                    error("create account request failed");
                    if(error) {
                        error()
                    }
                }
            }
        }
    });
}


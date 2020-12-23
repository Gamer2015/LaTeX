
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
                let subject = message.header.subject;
                if(subject == "response") {
                    let requestId = message.responseTo;
                    let request = messages[requestId];
                    delete messages[requestId];

                    if(
                        request.behavior != null 
                        && request.behavior.callback != null
                    ) {
                        request.behavior.callback(message, request);
                    }
                } else if(subject == "packages changed") {
                    refreshPackages(message.accountIds);
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

function refreshPackages(accountIds) {
    request = window.indexedDB.open('database').onsuccess = function(event) {
        let db = event.target.result;
        let transaction = db.transaction('accounts');
        let accounts = [];

        if(accountIds == null) {
            let index = transaction.objectStore('accounts').index('active');
            index.openCursor(IDBKeyRange.only('true')).onsuccess = function(event) {
                let cursor = event.target.result;
                if(cursor) {
                    accounts.push(cursor.value);
                    cursor.continue();
                }
            }   
        } else {
            if(Array.isArray(accountIds) == false) {
                accountIds = [accountIds]
            }
            if(accountIds.length == 0) {
                return;
            }

            for(let accountId of accountIds) {
                transaction.objectStore('accounts').get(accountId).onsuccess = function(event) {
                    accounts.push(event.target.result);
                }
            }
        }

        transaction.oncomplete = function(event) {
            if(accounts.length != 0) {
                websocket.send("get", {
                    accounts: accounts.map(function(account) { return {
                        id: account.id,
                        password: account.password,
                        timestamp: account.timestamp,
                    }}), behavior: {
                        accounts: accounts
                        , timestamp: Date.now()
                        , callback: function(serverData, clientData) {
                            if(serverData["status"] == "success") {
                                info("packages retrieved successfully", serverData.packages);

                                request = window.indexedDB.open('database')
                                request.onsuccess = function(event) {
                                    let db = request.result;
                                    let transaction = db.transaction(['accounts', 'packages'], 'readwrite')

                                    let accountMap = {};
                                    let accountStore = transaction.objectStore('accounts');
                                    for(let account of clientData.behavior.accounts) {
                                        account.timestamp = clientData.behavior.timestamp;
                                        accountStore.put(account);
                                        accountMap[account.id] = account;
                                    }

                                    let packageStore = transaction.objectStore('packages');
                                    for(let package of serverData.packages) {
                                        let account = accountMap[package.accountId];

                                        let record = {};
                                        record.accountId = package.accountId;
                                        record.crypto = JSON.parse(sjcl.decrypt(account.dataKey, package.crypto));
                                        record.data = sjcl.decrypt(account.dataKey, package.data);
                                        record.deleted = sjcl.decrypt(account.dataKey, package.deleted);
                                        record.key = sjcl.decrypt(account.dataKey, package.key, null, record.crypto);
                                        console.log(package.key, record.key);
                                        
                                        if(package.deleted == 'true') {
                                            packageStore.delete(record);
                                        } else {
                                            packageStore.put(record);
                                        }
                                    }
                                    transaction.oncomplete = function() {
                                        display();
                                    }
                                }
                            } else {
                                error("retrieving packages failed", clientData.accounts);
                                if(error) {
                                    error()
                                }
                            }
                        }
                    }
                });
            }
        };
    }
}

// server-side database operation integration
function savePackages(packages) {
    let accountIds = packages.map(function(package) {
        return package.accountId;
    });

    window.indexedDB.open('database').onsuccess = function(event) {
        let db = event.target.result;
        let transaction = db.transaction(['accounts', 'packages'], 'readwrite')
        let accountMap = {};
        let accounts = [];
        let accountsStore = transaction.objectStore('accounts');
        for(let accountId of accountIds) {
            accountsStore.get(accountId).onsuccess = function(event) {
                accounts.push(event.target.result);
                accountMap[accountId] = event.target.result;
            }
        }
        let packageStore = transaction.objectStore('packages');
        for(let package of packages) {
            packageStore.get([package.accountId, package.key]).onsuccess = function(event) {
                let tmp = event.target.result;
                if(package.deleted == null) {
                    package.deleted = tmp.deleted;
                }
                if(package.crypto == null) {
                    package.crypto = tmp.crypto;
                }

                if(package.deleted == 'true') {
                    packageStore.delete([package.accountId, package.key]);   
                } else {
                    packageStore.put(package);  
                }
            }
        }
        transaction.oncomplete = function() {
            display();
            if(accounts.length != 0) {
                websocket.send("save", {
                    accounts: accounts.map(function(account) { return {
                        id: account.id,
                        password: account.password
                    }}), packages: packages.map(function(package) { 
                        let account = accountMap[package.accountId];
                        if(package.crypto == null) {
                            package.crypto = {};
                        }
                        let record = {};
                        record.accountId = package.accountId;
                        record.key = sjcl.encrypt(account.dataKey, package.key, package.crypto, package.crypto);
                        record.data = sjcl.encrypt(account.dataKey, package.data);
                        record.crypto = sjcl.encrypt(account.dataKey, JSON.stringify(package.crypto));
                        record.deleted = sjcl.encrypt(account.dataKey, package.deleted);
                        console.log(package.key, record.key);

                        return record;
                    })
                    , timestamp: Date.now()
                });
            }
        }
    }
}

// server-side database operation integration
function authenticate(accounts) {
    if(accounts == null) {
        // authenticate all active accounts
        accounts = [];

        request = window.indexedDB.open('database').onsuccess = function(event) {
            let db = event.target.result;
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

    websocket.send("authenticate", {
        accounts: accounts.map(function(account) { return {
            id: account.id
            , password: account.password
        }})
        , behavior: {
            callback: function(serverData, clientData) {
                if(serverData["status"] == "success") {
                    info("authentication successful", clientData.accounts);

                    refreshPackages(accounts.map(function(account) {
                        return account.id;
                    }));
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
                            dataKey: calculateDataKey(secrets[i]),
                            timestamp: Date.now(),
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


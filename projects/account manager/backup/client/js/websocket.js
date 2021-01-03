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
                authenticate(true);
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
                        request.callback != null 
                        && request.callback.callback != null
                    ) {
                        request.callback.callback(message, request);
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
            if('callback' in message) {
                // expect a response to this message
                message.header.id = generateRequestId();
                messages[message.header.id] = message;

                message = JSON.parse(JSON.stringify(message));  
                delete message.callback; // remove callback data
            }
            
            socket.send(JSON.stringify(message));
            debug("sending message", message);
        },
    };
})();

function forceSet(entities) {
    if(typeof(entities) == 'string') {
        entities = new Set([entities]);
    }

    try {
        // support any iterable
        entities = new Set(entities);
    } catch(err) {
        // accountIds not iterable
        if(entities != true) {
            entities = new Set([entities]);
        }
    }
    return entities;
}

function getLocalAccountMap(accountIds, callback, transaction=null) {
    accountIds = forceSet(accountIds);

    if(transaction == null) {
        window.indexedDB.open('database').onsuccess = function(event) {
            let db = event.target.result;
            getLocalAccountMap(accountIds, callback, db.transaction('accounts'));
        }
        return;
    }

    let accountStore = transaction.objectStore('accounts');

    let accounts = {};
    if(accountIds == true) {
        transaction.objectStore('accounts').openCursor().onsuccess = function(event) {
            let cursor = event.target.result;
            if(cursor) {
                let account = cursor.value;
                accounts[account.id] = account;
                cursor.continue();
            }
        }
    } else {
        for(let accountId of accountIds) {
            accountStore.get(accountId).onsuccess = function(event) {
                let account = event.target.result;
                if(account != null) {
                    accounts[account.id] = account;
                }
            }
        } 
    }

    transaction.oncomplete = function(event) {
        if(callback) {
            callback(accounts);
        }
    }
}

function refreshPackagesCallback(serverData, clientData) {
    if(serverData.packages.length != 0) {
        info("packages retrieved successfully", serverData.packages);

        let successAccountIds = serverData.packages.reduce(function(accountIds, package) {
            accountIds.add(package.accountId);
            return accountIds;
        }, new Set());

        window.indexedDB.open('database').onsuccess = function(event) {
            let db = event.target.result;
            let transaction = db.transaction(['accounts', 'packages'], 'readwrite');


            let accountStore = transaction.objectStore('accounts');
            let accountMap = {};
            for(let account of clientData.callback.accounts) {
                if(successAccountIds.has(account.id)) {
                    // update timestamps of accounts that got new packages
                    upsert(accountStore, {
                        id: account.id,
                        timestamp: clientData.callback.timestamp
                    }); 
                    accountMap[account.id] = account;
                }
            }

            let packageStore = transaction.objectStore('packages');
            for(let package of serverData.packages) { 
                packageStore.put(unpackPackage(package, accountMap));
            }
            transaction.oncomplete = function() {
                display();
            }
        }
    }
    if(serverData.failed.length != 0) {
        error("retrieving packages failed", serverData.failed);
        if(error) {
            error()
        }
    }
}
function refreshPackagesFromMemory(accounts, callback=refreshPackagesCallback) {
    if(accounts.length == 0) {
        return;
    }        
    websocket.send("get", {
        accounts: prepareAccounts(accounts)
        , callback: {
            accounts: accounts
            , timestamp: Date.now()
            , callback: callback
        }
    });
}
function refreshPackages(accountIds) {
    getLocalAccountMap(accountIds, function(accountMap) {
        let accounts = Object.values(accountMap);
        refreshPackagesFromMemory(accounts);
    });
}

function shallowCopy(entity, fields) {
    let tmp = {};
    for(let field of fields) {
        if(field in entity) {
            tmp[field] = entity[field];
        }
    }
    return tmp;
}
function prepareSecrets(secrets) {
    return secrets.map(function(secret) {
        return calculatePassword(secret)
    });
}

function prepareAccounts(accounts) {
    return accounts.map(function(account) { 
        return shallowCopy(account, ["id", "password", "timestamp"]);
    });
}

let relevantPackageFields = ["accountId", "id", "timestamp", "data"];
let encryptedPackageFields = ["data"];
function preparePackages(packages, accountMap) {
    return packages.map(function(package) { 
        let account = accountMap[package.accountId];

        let tmp = shallowCopy(package, relevantPackageFields);
        for(let field of encryptedPackageFields) {
            tmp[field] = sjcl.encrypt(account.encryptionKey, JSON.stringify(tmp[field]));
        }

        return tmp;
    });
}
function unpackPackage(package, accountMap) {
    let account = accountMap[package.accountId];

    let tmp = shallowCopy(package, relevantPackageFields);
    for(let field of encryptedPackageFields) {
        tmp[field] = JSON.parse(sjcl.decrypt(account.encryptionKey, tmp[field]));
    }

    return tmp;
}

function upsert(store, entries) {
    let keyPath = store.keyPath;
    if(Array.isArray(keyPath) == false) {
        keyPath = [keyPath];
    }
    if(Array.isArray(entries) == false) {
        entries = [entries];
    }
    for(let entry of entries) {
        key = keyPath.map(function(key) { return entry[key]; });
        if(keyPath.length == 1) {
            key = key[0];
        }

        store.get(key).onsuccess = function(event) {
            let existing = event.target.result;
            if(existing == null) {
                // insert if not existing
                existing = entry;
            }

            if(entry._delete != null) {
                for(let keyPath of entry._delete) {
                    let keys = keyPath.split(".");
                    let tmp = existing;
                    for(let i = 0; i < keys.split() - 1; ++i) {
                        tmp = tmp[keys[i]];
                    }
                    delete tmp[key[i]];
                }
                delete entry._delete;
            }

            for(let key in entry) {
                existing[key] = entry[key];
            }
            store.put(existing);  
        }
    }
}

// server-side database operation integration
function savePackages(packages) {
    if(Array.isArray(packages) == false) {
        packages = [packages];
    }
    let accountIds = packages.map(function(package) {
        return package.accountId;
    });

    if(packages.length == 0 || accountIds.length == 0) {
        return;
    }

    window.indexedDB.open('database').onsuccess = function(event) {
        let db = event.target.result;

        let accounts = {};
        getLocalAccountMap(accountIds, function(accountMap) {
            accounts = accountMap;

            { // only process packages with a valid account attached
                let invalidAccounts = [];
                let validPackages = [];
                for(let package of packages) {
                    if(package.accountId in accounts == false) {
                        invalidAccounts.push(package);
                    } else {
                        validPackages.push(package);
                    }
                }
                if(invalidAccounts.length != 0) {
                    warning("invalid accounts for packages: ", invalidAccounts);
                }
                packages = validPackages;
            }

            display();
            if(packages.length == 0) {
                return;
            }
            websocket.send("save", {
                accounts: prepareAccounts(Object.values(accounts))
                , packages: preparePackages(packages, accounts)
                , timestamp: Date.now()
                , callback: {
                    accounts: accounts
                    , callback: function(serverData, clientData) {  
                        if(serverData.successful.length != 0) {
                            info("packages saved successfully", serverData.successful);
                        } 
                        if(serverData.failed.length != 0) {
                            error("saving packages failed", serverData.failed);
                        }
                    }
                }
            }); 
        }, db.transaction('accounts'));
    }
}

// server-side database operation integration
function authenticationCallback(serverData, clientData) {
    if(serverData.successful.length != 0) {
        info("authentication successful", serverData.successful);

        refreshPackages(serverData.successful.map(function(account) {
            return account.id;
        }));
    }
    if(serverData.failed.length != 0) {
        error("authentication request failed", serverData.failed);
        if(error) {
            error()
        }
    }
}
function authenticateFromMemory(accounts, callback=authenticationCallback) {
    if(accounts.length == 0) {
        return;
    }
    websocket.send("authenticate", {
        accounts: prepareAccounts(accounts)
        , callback: {
            callback: callback
        }
    });
}
function authenticate(accountIds, callback) {
    getLocalAccountMap(accountIds, function(accountMap) {
        let accounts = Object.values(accountMap);
        authenticateFromMemory(accounts, callback);
    });
}


// used in import accounts, simulating a server response
function requestAccountsCallback(serverData, clientData) {
    if(serverData.accounts.length != clientData.callback.accounts.length) {
        warning("not all accounts were inserted successfully, only storing those that were ..");
    }


    let createdAccounts = [];
    for(let i = 0; i < serverData.accounts.length; ++i) {
        let accountId = serverData.accounts[i].id;
        if(accountId == null) {
            // not inserted successfully
            continue;
        }

        let account = clientData.callback.accounts[i];
        account.id = accountId;
        createdAccounts.push(account);
    }

    request = window.indexedDB.open('database');
    request.onsuccess = function(event) {
        let db = request.result;
        let transaction = db.transaction('accounts', 'readwrite');

        let store = transaction.objectStore('accounts');
        for(let account of createdAccounts) {
            store.put(account);
        }

        transaction.oncomplete = function(event) {
            info("new accounts: ", createdAccounts);
            authenticate(createdAccounts.map(function(account) {
                return account.id;
            }));

            if(clientData.callback.success) {
                clientData.callback.success(createdAccounts);
            }
        };
    }
}

function populateAccountKeyFields(accounts) {
    return accounts.map(function(account) { 
        account.password = calculatePassword(account.secret);
        account.encryptionKey = calculateEncryptionKey(account.secret);
        return account;
    });
}
// server-side database operation integration
function requestAccounts(success, error, number=1) {
    let accounts = generateSecrets(number).map(function(secret) { 
        return populateAccountKeyFields([{
            secret: secret,
        }])[0];
    });
    // sjcl.decrypt("password", "encrypted-data")

    websocket.send("create accounts", {
        accounts: prepareAccounts(accounts)
        , callback: {
            accounts: accounts
            , success: success
            , error: error
            , callback: requestAccountsCallback
        }
    });
}


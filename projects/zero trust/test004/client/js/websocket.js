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
                delete message.callback; // not needed information should be stored on device
            }
            
            socket.send(JSON.stringify(message));
            debug("sending message", message);
        },
    };
})();

function refreshPackages(accountIds) {
    getLocalAccountMap(accountIds, function(accountMap) {
        let accounts = Object.values(accountMap);

        if(accounts.length == 0) {
            return;
        }
        websocket.send("get", {
            accounts: prepareAccounts(accounts)
            , callback: {
                accounts: accounts
                , timestamp: Date.now()
                , callback: function(serverData, clientData) {
                    if(serverData.packages.length != 0) {
                        info("packages retrieved successfully", serverData.packages);

                        window.indexedDB.open('database').onsuccess = function(event) {
                            let db = event.target.result;
                            let transaction = db.transaction(['accounts', 'packages'], 'readwrite');

                            let accountStore = transaction.objectStore('accounts');
                            let accountMap = {};
                            for(let account of clientData.callback.accounts) {
                                // update timestamp
                                upsert(accountStore, {
                                    id: account.id,
                                    timestamp: clientData.callback.timestamp
                                }); 
                                accountMap[account.id] = account;
                            }

                            let packageStore = transaction.objectStore('packages');
                            for(let package of serverData.packages) { 
                                let account = accountMap[package.accountId];
                                let metadataFields = ["accountId", "id", "timestamp"];

                                console.log("metadata", prepare(package, metadataFields));
                                console.log("data", package.data);
                                console.log("encryptionKey", account.encryptionKey);
                                let tmp = Object.assign(JSON.parse(sjcl.decrypt(
                                    account.encryptionKey, package.data
                                )), prepare(package, metadataFields));
                                console.log("tmp", tmp);
                                
                                packageStore.put(tmp);
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
            }
        });
    });
}

function getLocalAccountMap(accountIds, callback, transaction=null) {
    if(typeof(accountIds) == 'string') {
        accountIds = new Set([accountIds]);
    }

    try {
        // support any iterable
        accountIds = new Set(accountIds);
    } catch(err) {
        // accountIds not iterable
        if(accountIds != true) {
            accountIds = new Set([accountIds]);
        }
    }

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
        let index = transaction.objectStore('accounts').index('active');
        index.openCursor(IDBKeyRange.only(indexedDbTrue)).onsuccess = function(event) {
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

function prepare(entity, fields) {
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
        return prepare(account, ["id", "password", "timestamp"]);
    });
}

function preparePackages(packages, accounts) {
    return packages.map(function(package) { 
        let account = accounts[package.accountId];
        let metadataFields = ["accountId", "id", "_id", "timestamp"];

        let tmp = Object.assign({}, package);
        for(let field of metadataFields) {
            delete tmp[field];
        }
        console.log("tmp", JSON.parse(JSON.stringify(tmp)));
        console.log("encryptionKey", account.encryptionKey);
        tmp = Object.assign({
            data: sjcl.encrypt(account.encryptionKey, JSON.stringify(tmp))
        }, prepare(package, metadataFields));
        console.log("tmp", JSON.parse(JSON.stringify(tmp)));

        return tmp;
    });
}

function populateNewPackageIds(packages, callback) {
    let unpopulatedCount = 0;
    for(let package of packages) {
        if(package.id == null || package.id.length == 0) {
            ++unpopulatedCount;
        }
    }

    // get temporary package ids
    let packageIds = new Set();

    window.indexedDB.open('database').onsuccess = function(event) {
        let db = event.target.result;
        let transaction = db.transaction('packages');
        let packageStore = transaction.objectStore('packages');

        // we need to get all the ids anyway, might as well do so in one go
        packageStore.openCursor().onsuccess = function(event) {
            let cursor = event.target.result;
            if(cursor) {
                let package = cursor.value;
                packageIds.add(package.id);
                cursor.continue();  
            }
        }

        transaction.oncomplete = function() {
            for(let package of packages) {
                let tmpId;
                if(package.id == null || package.id.length == 0) {
                    let tmpId = 0;
                    while(tmpId == 0 || packageIds.has(tmpId)) {
                        tmpId = generateRandom(packageIdLength);
                    }

                    package.id = tmpId; 
                    package._id = tmpId;
                    packageIds.add(tmpId); 
                }
            }

            if(callback) {
                callback(packages);
            }
        }
    }
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

function resolveInsertedPackagesCallback(serverData, clientData) {
    let successful = serverData.successful;
    let failed = serverData.failed;

    window.indexedDB.open('database').onsuccess = function(event) {
        let db = event.target.result;
        let transaction = db.transaction('packages', 'readwrite');
        packageStore = transaction.objectStore('packages');
            
        let createdPackages = successful.filter(function(package) { 
            return package._id != null && package._id.length != 0;
        });
        for(let package of createdPackages) {
            let key = [package.accountId, package._id];
            packageStore.get(key).onsuccess = function(event) {
                let existing = event.target.result;
                delete existing._id;
                existing.id = package.id;

                packageStore.put(existing);  
                packageStore.delete(key);
            }
            delete package._id;
        }

        let insertionFailedPackages = failed.filter(function(package) { 
            return package._id != null && package._id.length != 0;
        });
        for(let package of insertionFailedPackages) {
            let key = [package.accountId, package._id];
            packageStore.delete(key);
            delete package._id;
        }
        transaction.oncomplete = function() {
            display();
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

    populateNewPackageIds(packages, function(packages) {
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

                let transaction = db.transaction('packages', 'readwrite')
                let packageStore = transaction.objectStore('packages');
                for(let package of packages) {
                    if(package._id != null) {
                        // new package, set default values and store
                        packageStore.add(package);  
                    } else { // existing package, save changes 
                        upsert(packageStore, package);
                    }
                }
                transaction.oncomplete = function() {
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
                                resolveInsertedPackagesCallback(serverData, clientData);    
                                if(serverData.successful.length != 0) {
                                    info("packages saved successfully", serverData.successful);
                                } 
                                if(serverData.failed.length != 0) {
                                    error("saving packages failed", serverData.failed);
                                }
                            }
                        }
                    });
                }
            }, db.transaction('accounts'));
        }
    });
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
function authenticate(accountIds) {
    getLocalAccountMap(accountIds, function(accountMap) {
        let accounts = Object.values(accountMap);

        if(accounts.length == 0) {
            return;
        }
        websocket.send("authenticate", {
            accounts: prepareAccounts(accounts)
            , callback: {
                callback: authenticationCallback
            }
        });
    });
}


// 
function requestAccountsCallback(serverData, clientData) {
    let secrets = clientData.callback.secrets;
    if(serverData.successful.length != secrets.length) {
        error("not all inserts were successful, abort ...");
        return;
    }

    let createdAccounts = [];
    for(let i = 0; i < serverData.successful.length; ++i) {
        createdAccounts.push({
            id: serverData.successful[i].id,
            secret: secrets[i],
            password: clientData.passwords[i],
            encryptionKey: calculateEncryptionKey(secrets[i]),
            timestamp: 0,
            active: indexedDbTrue,
        });
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
// server-side database operation integration
function requestAccounts(success, error, number=1) {
    let secrets = generateSecrets(number);
    let passwords = secrets.map(function(secret) {
        return calculatePassword(secret);
    });
    // sjcl.decrypt("password", "encrypted-data")

    websocket.send("create accounts", {
        passwords: passwords
        , callback: {
            secrets: secrets
            , success: success
            , error: error
            , callback: requestAccountsCallback
        }
    });
}


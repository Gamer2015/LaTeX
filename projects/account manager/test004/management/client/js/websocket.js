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
                    refreshPackagesFromMemory(message.usernames.map(
                        function(username) { return {
                            username: username
                        }}
                    ));
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
/* 
function refreshPackages(accountIds) {
    getLocalAccountMap(accountIds, function(accountMap) {
        let accounts = Object.values(accountMap);
        refreshPackagesFromMemory(accounts);
    });
}
*/

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
        return shallowCopy(account, ["username", "password", "timestamp"]);
    });
}

let relevantPackageFields = ["username", "id", "data", "key"];
let encryptedPackageFields = ["data"];
let packageKeyField = "key";
function preparePackages(packages, accountMap) {
    return packages.map(function(package) { 
        let account = accountMap[package.username];

        let tmp = shallowCopy(package, relevantPackageFields);
        for(let field of encryptedPackageFields) {
            tmp[field] = sjcl.encrypt(tmp.key, JSON.stringify(tmp[field]));
        }
        tmp.key = sjcl.encrypt(account.key, tmp.key);

        return tmp;
    });
}
function unpackPackage(package, account) {
    let tmp = shallowCopy(package, relevantPackageFields);
    tmp.key = sjcl.decrypt(account.key, tmp.key);
    for(let field of encryptedPackageFields) {
        tmp[field] = JSON.parse(sjcl.decrypt(tmp.key, tmp[field]));
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

/* probably not useful anymore
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
}*/

function createLoginsCallback(serverData, clientData) {
    if(serverData.logins.length != 0) {
        info("retrieved logins", serverData.logins);
        let usersChanged = serverData.logins.reduce(function(usernames, login) {
            usernames.add(login.username);
            return usernames;
        }, new Set());

        let storedAccounts = getAccounts(usersChanged);
        let packages = [];
        for(let login of serverData.logins) {
            let account = storedAccounts[login.username];
            // create packages from logins
            packages.push({
                username: login.username,
                data: {
                    login: {
                        id: login.id
                    }
                }
            });
        }
        
        savePackages(packages);
    }
    if(serverData.failed.length != 0) {
        error("retrieving logins failed", serverData.failed);
        if(clientData.callback.onerror) {
            clientData.callback.onerror(serverData, clientData);
        }
    }
}
function createLogins(accounts, amount=1, onsuccess=null, onerror=null, callback=createLoginsCallback) {
    if(accounts.length == 0 || amount == 0) {
        return;
    }        
    accounts = Array.from(Object.values(getAccounts(accounts.map(function(account) { 
        return account.username;
    }))));
    websocket.send("create logins", {
        accounts: prepareAccounts(accounts)
        , amount: amount
        , callback: {
            onsuccess: onsuccess
            , onerror: onerror
            , callback: callback
        }
    });
}

// server-side database operation integration
function savePackages(packages) {
    if(Array.isArray(packages) == false) {
        packages = [packages];
    }
    let usernames = packages.map(function(package) {
        return package.username;
    });

    if(packages.length == 0 || usernames.length == 0) {
        return;
    }
    for(let package of packages) {
        if(package.key == null) {
            package.key = createPackageKeys(1)[0];
        }
    }

    let accounts = getAccounts(usernames);
    { // only process packages with a valid account attached
        let invalidAccounts = [];
        let validPackages = [];
        for(let package of packages) {
            if(package.username in accounts == false) {
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

    if(packages.length == 0) {
        return;
    }
    websocket.send("save", {
        accounts: prepareAccounts(Object.values(accounts))
        , packages: preparePackages(packages, accounts)
        , timestamp: Date.now()
        , callback: {
            callback: function(serverData, clientData) {  
                let successful = [];
                let failed = [];
                for(let packageEntity in serverData.packages) {
                    let entity = packageEntity.entity;
                    if(packageEntity.status == 'success') {
                        successful.push(entity);
                    } else if(packageEntity.status == 'failed') {
                        failed.push(entity);
                    }
                }
                if(successful.length != 0) {
                    info("packages saved successfully", serverData.successful);
                } 
                if(failed.length != 0) {
                    error("saving packages failed", serverData.failed);
                }
            }
        }
    }); 
}

function refreshPackagesCallback(serverData, clientData) {
    if(serverData.packages.length == 0 && serverData.failed.length == 0) {
        // retrieved all successfully
        if(clientData.callback.onsuccess) {
            clientData.callback.onsuccess(serverData, clientData);
        }
    }
    if(serverData.packages.length != 0) {
        info("retrieved packages", serverData.packages);
        let usersChanged = serverData.packages.reduce(function(usernames, package) {
            usernames.add(package.username);
            return usernames;
        }, new Set());

        let storedAccounts = getAccounts(usersChanged);
        for(let username of usersChanged) {
            let account = storedAccounts[username];
            if(account != null) { 
                // update timestamps of accounts 
                account.timestamp = clientData.callback.timestamp;
            }
        }

        for(let package of serverData.packages) {
            let account = storedAccounts[package.username];
            // decrypt package
            package = unpackPackage(package, account);
            if(account.packages == null) {
                account.packages = {};
            }
            account.packages[package.id] = package;
        }

        storeAccounts(Object.values(storedAccounts));
        display();
        // at least some new package or login
        if(clientData.callback.onsuccess) {
            clientData.callback.onsuccess(serverData, clientData);
        }
    }

    if(serverData.failed.length != 0) {
        error("retrieving packages failed", serverData.failed);
        if(clientData.callback.onerror) {
            clientData.callback.onerror(serverData, clientData);
        }
    }
}
function refreshPackagesFromMemory(accounts, onsuccess=null, onerror=null, callback=refreshPackagesCallback) {
    if(accounts.length == 0) {
        return;
    }        
    accounts = Array.from(Object.values(getAccounts(accounts.map(function(account) { 
        return account.username;
    }))));
    websocket.send("get", {
        accounts: prepareAccounts(accounts)
        , callback: {
            timestamp: Date.now()
            , onsuccess: onsuccess
            , onerror: onerror
            , callback: callback
        }
    });
}

function populateAccountKeyFields(accounts) {
    return accounts.map(function(account) { 
        account.password = calculatePassword(account.secret);
        account.key = calculateAccountKey(account.secret);
        return account;
    });
}

// server-side database operation integration
function authenticationCallback(serverData, clientData) {
    if(serverData.successful.length != 0) {
        info("authentication successful", serverData.successful);

        let accountMap = {};
        for(let account of clientData.callback.accounts) {
            accountMap[account.username] = account;
        }

        let successAccounts = {};
        for(let i = 0; i < serverData.successful.length; ++i) {
            let username = serverData.successful[i].username;
            successAccounts[username] = accountMap[username];
        }

        let accounts = Array.from(Object.values(successAccounts))
        storeAccounts(accounts);
        display();

        refreshPackagesFromMemory(
            accounts
            , clientData.callback.onsuccess
            , clientData.callback.onerror
        );
    }
    if(serverData.failed.length != 0) {
        error("authentication request failed", serverData.failed);
        if(clientData.callback.onerror) {
            clientData.callback.onerror(serverData, clientData);
        }
    }
}
function authenticateFromMemory(accounts, onsuccess=null, onerror=null, callback=authenticationCallback) {
    if(accounts.length == 0) {
        return;
    }
    accounts = populateAccountKeyFields(accounts);

    websocket.send("authenticate", {
        accounts: prepareAccounts(accounts)
        , callback: {
            accounts: accounts
            , onsuccess: onsuccess
            , onerror: onerror
            , callback: callback
        }
    });
}
/* not seeing how this could be used in the future
function authenticate(accountIds, callback) {
    getLocalAccountMap(accountIds, function(accountMap) {
        let accounts = Object.values(accountMap);
        authenticateFromMemory(accounts, callback);
    });
}
*/

// used in import accounts, simulating a server response
function requestAccountsCallback(serverData, clientData) {
    let createdAccounts = [];
    for(let i = 0; i < serverData.accounts.length; ++i) {
        let accountEntity = serverData.accounts[i];
        if(accountEntity.status == "success") {
            let account = clientData.callback.accounts[i];
            createdAccounts.push(account);
        } else if(accountEntity.status == "failed") {
            if(accountEntity.reason == "username is already taken") {
                console.warn("username already taken");
            } else {
                console.err("an unknown error occured");
            }
            // not inserted successfully
            continue;
        }
    }

    if(createdAccounts.length != 0) {
        authenticateFromMemory(
            createdAccounts
            , clientData.callback.onsuccess
            , clientData.callback.onerror
        );
    }
    if(createdAccounts.length != clientData.accounts.length) {
        // something went subtly wrong
        if(clientData.callback.onerror) {
            clientData.callback.onerror(serverData, clientData);
        }
    }
}

function requestAccountsFromMemory(accounts, onsuccess=null, onerror=null, callback=requestAccountsCallback) {
    if(accounts.length == 0) {
        return;
    }
    accounts = populateAccountKeyFields(accounts);
    websocket.send("create accounts", {
        accounts: prepareAccounts(accounts)
        , callback: {
            accounts: accounts
            , onsuccess: onsuccess
            , onerror: onerror
            , callback: callback
        }
    });
}
// server-side database operation integration
/* not seeing how this could be used in the future
function requestAccounts(success, error, number=1) {
    let accounts = generateSecrets(number).map(function(secret) { return {
        secret: secret,
    }});
    requestAccountsFromMemory(accounts);
}
*/
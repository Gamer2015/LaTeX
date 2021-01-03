function displayId(id) {
    return idEncoding.encode(BigInt(('0x'+id))); 
}
function displayId2hex(id) {
    let tmp = idEncoding.decode(id).toString(16); 
    return tmp;
}

function display() {
    let accountList = document.createElement('ol');    
    {
        let listenerDiv = document.getElementById('accounts'); 
        listenerDiv.innerHTML = '';
        listenerDiv.appendChild(accountList);  
    }

    let packageList = document.createElement('ol');       
    {
        let listenerDiv = document.getElementById('packages'); 
        listenerDiv.innerHTML = '';
        listenerDiv.appendChild(packageList);  
    }

    request = window.indexedDB.open('database')
    request.onsuccess = function(event) {
        let db = request.result;
        let transaction = db.transaction(['accounts', 'packages'])
        transaction.objectStore('accounts').openCursor().onsuccess = function(event) {
            let cursor = event.target.result;
            if(cursor) {
                let account = cursor.value;
                let listItem = document.createElement('li');

                listItem.innerHTML = '<span style="font-family: monospace">'
                    + 'AccountId: ' + account.id + '<br/>Secret: ' + account.secret+'</span><br/><br/>' ;
                accountList.appendChild(listItem);  

                cursor.continue();
            }
        }   
        transaction.objectStore('packages').openCursor().onsuccess = function(event) {
            let cursor = event.target.result;
            if(cursor) {
                let package = cursor.value;
                let listItem = document.createElement('li');

                listItem.innerHTML = '<span style="font-family: monospace">'
                    + 'AccountId: ' + package.accountId + "<br/>"
                    + "PackageId: " + package.id+'</span><br/>'
                    + 'Data: ' + package.data + '<br/><br/>' ;
                packageList.appendChild(listItem);  

                cursor.continue();
            }
        }   
    }
}

function importAccount() {

    let accounts = [{
        id: document.getElementById('importAccountId').value,
        secret: document.getElementById('importAccountSecret').value
    }];
    populateAccountKeyFields(accounts);

    authenticateFromMemory(accounts, function(serverData, clientData) {
        if(serverData.successful.length != 0) {
            info("authentication successful", serverData.successful);

            requestAccountsCallback({
                accounts: accounts.map(function(account) { return {
                    id: account.id
                }}),
            }, {
                callback: {
                    accounts: accounts
                    , success: function(accounts) {
                        display();
                    }
                }
            });
        } 
        if(serverData.failed.length != 0) {
            error("authentication request failed", serverData.failed);
        }
    })
}
//
function createAccount() {
    let accounts = [{
        username: document.getElementById('createUsername').value,
        secret: document.getElementById('createSecret').value
    }];

    requestAccountsFromMemory(accounts, function(accounts) {
        display();
    });
}

// 
function savePackage() {
    let package = {
        accountId: document.getElementById('accountId').value,
        id: document.getElementById('packageId').value,
        data: document.getElementById('packageData').value
    }
    savePackages([package]);
}
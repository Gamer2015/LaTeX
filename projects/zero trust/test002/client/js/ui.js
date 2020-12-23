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
        let index = transaction.objectStore('accounts').index('active');
        index.openCursor(IDBKeyRange.only('true')).onsuccess = function(event) {
            let cursor = event.target.result;
            if(cursor) {
                let account = cursor.value;
                let listItem = document.createElement('li');

                listItem.innerHTML = '<span style="font-family: monospace">'
                    + account.displayName + ' ' + account.id + ' ' + displayId(account.id)
                    + '</br>' + account.secret+'</span>' ;
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
                    + package.key + ' ' + package.data + '</span>' ;
                packageList.appendChild(listItem);  

                cursor.continue();
            }
        }   
    }
}

function importAccount() {
    let account = {
        id: document.getElementById('importAccountId').value,
        secret: document.getElementById('importAccountSecret').value,
        displayName: document.getElementById('importAccountName').value,
        timestamp: 0,
        active: 'true',
    };
    account.password = calculatePassword(account.secret);
    account.dataKey = calculateDataKey(account.secret);

    request = window.indexedDB.open('database')
    request.onsuccess = function(event) {
        let db = request.result;
        let transaction = db.transaction(['accounts'], 'readwrite');
        transaction.objectStore('accounts').put(account);
        
        transaction.oncomplete = function(event) {
            display();
            authenticate(account);
        };
    }
}
//
function createAccount() {
    let label = document.getElementById('accountLabel').value;

    requestAccounts(function(accounts) {
        accounts[0].displayName = label;

        request = window.indexedDB.open('database')
        request.onsuccess = function(event) {
            let db = request.result;
            let transaction = db.transaction(['accounts'], 'readwrite');
            transaction.oncomplete = function(event) {
                display()
            };
            let store = transaction.objectStore('accounts');
            for(let account of accounts) {
                store.put(account);
            }
        }
    });
}

// 
function savePackage() {
    let package = {
        accountId: document.getElementById('accountId').value,
        key: document.getElementById('packageKey').value,
        data: document.getElementById('packageData').value
    }
    savePackages([package]);
}
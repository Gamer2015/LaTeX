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
        index.openCursor(IDBKeyRange.only(indexedDbTrue)).onsuccess = function(event) {
            let cursor = event.target.result;
            if(cursor) {
                let account = cursor.value;
                let listItem = document.createElement('li');

                listItem.innerHTML = '<span style="font-family: monospace">'
                    + 'Account Id: ' + account.id + '; Secret: ' + account.secret+'</span><br/><br/>' ;
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
                    + 'Account Id: ' + package.accountId + "; Package Id: " + package.id+'</span><br/>'
                    + package.data + '<br/><br/>' ;
                packageList.appendChild(listItem);  

                cursor.continue();
            }
        }   
    }
}

function importAccount() {
    let id = document.getElementById('importAccountId').value;
    let secret = document.getElementById('importAccountSecret').value;
    let password = calculatePassword(secret);

    requestAccountsCallback({
        successful: [{id: id}],
    }, {
        passwords: [password]
        , callback: {
            secrets: [secret]
            , success: function(accounts) {
                display();
            }
        }
    });
}
//
function createAccount() {
    requestAccounts(function(accounts) {
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
function displayId(id) {
    return idEncoding.encode(BigInt(('0x'+id))); 
}
function displayId2hex(id) {
    let tmp = idEncoding.decode(id).toString(16); 
    return tmp;
}

function display() {
    let list = document.createElement('ol');    
    let listenerDiv = document.getElementById('accounts'); 
    listenerDiv.innerHTML = '';
    listenerDiv.appendChild(list);  

    request = window.indexedDB.open('database')
    request.onsuccess = function(event) {
        let db = request.result;
        let index = db.transaction('accounts').objectStore('accounts').index('active');
        index.openCursor(IDBKeyRange.only('true')).onsuccess = function(event) {
            let cursor = event.target.result;
            if(cursor) {
                let account = cursor.value;
                let listItem = document.createElement('li');

                listItem.innerHTML = '<span style="font-family: monospace">'
                    + account.displayName + ' ' + account.id + ' ' + displayId(account.id)
                    + '</br>' + account.secret+'</span>' ;
                list.appendChild(listItem);  

                cursor.continue();
            }
        }   
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
function sendMessageRequest() {
    let senderId = document.getElementById('senderId').value;
    let receiverId = document.getElementById('receiverId').value;
    let message = document.getElementById('message').value;

    if(senderId == '') {
        requestChannel(function(channel) {
            display();  
            sendMessage(channel.id, receiverId, message);    
        });
    } else {
        sendMessage(senderId, receiverId, message);
    }
}
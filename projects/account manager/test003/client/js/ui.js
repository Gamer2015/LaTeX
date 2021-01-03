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

    let currentlySelected = document.getElementById('account');

    let packageList = document.createElement('ol');       
    {
        let listenerDiv = document.getElementById('packages'); 
        listenerDiv.innerHTML = '';
        listenerDiv.appendChild(packageList);  
    }

    let accounts = Array.from(Object.values(getAccounts(true)));
    for(let account of accounts) {
        let listItem = document.createElement('li');

        listItem.innerHTML = '<span style="font-family: monospace">'
            + 'Username: ' + account.username + '<br/>Secret: ' + account.secret+'</span><br/><br/>' ;
        accountList.appendChild(listItem);  
    }  

    for(let account of accounts) {
        let accountPackageListItem = document.createElement('li');
        packageList.appendChild(accountPackageListItem);
        let accountUsernameItem = document.createElement("h3");
        accountUsernameItem.onclick = function() {
            savePackage({
                username: account.username,
                data: "test"
            }, function() {
                display();
            });
        };
        accountUsernameItem.innerHTML = account.username;
        accountPackageListItem.appendChild(accountUsernameItem);

        let accountPackageList = document.createElement('ol');
        accountPackageListItem.appendChild(accountPackageList);

        if("packages" in account == false) {
            continue;
        }

        for(let package of Object.values(account.packages)) {
            let listItem = document.createElement('li');

            listItem.innerHTML = '<span style="font-family: monospace">'
                + 'User: ' + package.username + '<br/>packageId: ' + package.packageId+'</span><br/>'
                + package.data + '<br/><br/>' ;
            accountPackageList.appendChild(listItem);  
        }
    }
}

function uiLogin() {
    let accounts = [{
        username: document.getElementById('loginUsername').value,
        secret: document.getElementById('loginSecret').value
    }];

    authenticateFromMemory(accounts, function() {
        console.log("hi, login successful");
        document.getElementById('login').style.display = "none";
        document.getElementById('logout').style.display = "inherit";
    });
}

function uiLogout(usernames) {
    logout(usernames);
    document.getElementById('login').style.display = "inherit";
    document.getElementById('logout').style.display = "none";
    display();
}

function createAccount() {
    let accounts = [{
        username: document.getElementById('createUsername').value,
        secret: document.getElementById('createSecret').value
    }];

    requestAccountsFromMemory(accounts);
}

// 
function savePackage(package, onsuccess=null) {
    savePackages([package], onsuccess);
}
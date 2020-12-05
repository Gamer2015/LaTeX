let channels = [];

function displayId(id) {
    return idEncoding.encode(BigInt(('0x'+id))); 
}
function displayId2hex(id) {
    let tmp = idEncoding.decode(id).toString(16); 
    return tmp;
}

function display() {
    let list = document.createElement('ol');    
    let listenerDiv = document.getElementById('channels'); 
    listenerDiv.innerHTML = '';
    listenerDiv.appendChild(list);  
    for(let channel of channels) {
        let listItem = document.createElement('li');

        listItem.innerHTML = '<span style="font-family: monospace">'+channel.id + ' ' + displayId(channel.id)+'</span>' + ',' + channel.password; //base58.encode(BigInt(('0x'+cursor.value.id))).padStart(11, '1'); // + ', ' + cursor.value.secret;
        list.appendChild(listItem);  
    }
}


// 
function createChannel() {  
    requestChannel(function() {
        display();
    });
}

// 
function sendMessage() {
    let senderId = document.getElementById('senderId').value;
    let receiverName = document.getElementById('receiverName').value;
    let receiverId = document.getElementById('receiverId').value;
    let message = document.getElementById('message').value;

    if(senderId == '') {
        requestChannel(receiverName, function(channel) {
            display();  
            sendMessageRequest(channel.id, receiverId, message);    
        });
    } else {
        sendMessageRequest(senderId, receiverId, message);
    }
}
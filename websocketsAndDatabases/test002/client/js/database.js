let database = (function() {
	let db = null;

	return {
		storeChannel: function(channel) {
			let transaction = db.transaction(['channels'], 'readwrite');
			let store = transaction.objectStore('channels');
			
			let request = store.add(channel);
			request.onerror = function(e) {
				error('Error', e.target.error.name);
			};
			request.onsuccess = function(e) {
		    	info('Channel stored successfully:', channel);	
		    	channels.push(channel);
			};
		},
		getChannels: function() {
			var transaction = db.transaction(["channels"], 'readonly');
			var objectStore = transaction.objectStore("channels");
			var request = objectStore.get(id);
			request.onerror = function(event) {
			  error('Error', event.target.error.name);
			};
			request.onsuccess = function(event) {
				if(callback) {
					callback(request);
				}
			};
		},
		load: function() {
			let tx = db.transaction("channels", "readonly");
			let store = tx.objectStore("channels");

			store.openCursor().onsuccess = function(event) {
				let cursor = event.target.result;
				if(cursor) {
					channels.push(cursor.value);
					cursor.continue();
				}
			}	
		},
		init: function() {
			if (!('indexedDB' in window)) {
				error('This browser doesn\'t support IndexedDB');
				return;
			}
			
			// Open our database; it is created if it doesn't already exist (see onupgradeneeded below)
			let request = window.indexedDB.open('channelDb', 1);

			request.onerror = function() {
				error('Database failed to open');
			};
			request.onsuccess = function() {
				info('Database opened successfully');
				db = request.result;
				this.load();
		    	// display();	
			};

			// Setup the database tables if this has not already been done
			request.onupgradeneeded = function(event) {
				var db = request.result;
				if (event.oldVersion < 1) {
		    		// Version 1 is the first version of the database.
		    		var channels = db.createObjectStore("channels", {keyPath: "id"}); // retrieve and send messages over this channel
		    	}
		    }
		}
	};
})()



function getChannelData(id, callback) {
	var transaction = db.transaction(["channels"], 'readonly');
	var objectStore = transaction.objectStore("channels");
	var request = objectStore.get(id);
	request.onerror = function(event) {
	  error('Error', event.target.error.name);
	};
	request.onsuccess = function(event) {
		if(callback) {
			callback(request);
		}
	};
}

function storeChannel(channel) {
	let transaction = db.transaction(['channels'], 'readwrite');
	let store = transaction.objectStore('channels');
	
	let request = store.add(channel);
	request.onerror = function(e) {
		error('Error', e.target.error.name);
	};
	request.onsuccess = function(e) {
    	info('Channel stored successfully:', channel);	
	};
}

//
function sendMessageRequest(from, to, message) {
	getChannelData(from, function(request) {
	    let xhttp = new XMLHttpRequest();
	    xhttp.onreadystatechange = function() {
	    	if (this.readyState == 4 && this.status == 200) {
	    		let response = JSON.parse(this.responseText);
	    		console.log("rows:", response);
	    	}
	    };
	    // console.log(request.result.secret, to, message);
	    xhttp.open("POST", "database/sendMessage.php", true);
		xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
		xhttp.send("from="+from+"&password="+request.result.password+"&to="+to+"&message="+message);	
	});
}


// prepare local storage 
function prepareLocalStorage() {
	if (!('indexedDB' in window)) {
		error('This browser doesn\'t support IndexedDB');
		return;
	}
	
	// Open our database; it is created if it doesn't already exist (see onupgradeneeded below)
	let request = window.indexedDB.open('channelDb', 1);

	request.onerror = function() {
		error('Database failed to open');
	};
	request.onsuccess = function() {
		info('Database opened successfully');
		db = request.result;

    	display();	
	};

	// Setup the database tables if this has not already been done
	request.onupgradeneeded = function(event) {
		var db = request.result;
		if (event.oldVersion < 1) {
    		// Version 1 is the first version of the database.
    		var channels = db.createObjectStore("channels", {keyPath: "id"}); // retrieve and send messages over this channel
    	}
    }
}
//


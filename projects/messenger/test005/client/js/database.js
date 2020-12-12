let messengerDatabase = 'messenger'
let channelStoreName = 'channels'

let database = (function() {
	let upgrades = [];

	let ObjectStore = function(_database, _storeName, _keyField) {
		let database = _database;
		let name = _storeName;
		let keyField = _keyField;
		let indexes = {};
		indexes[keyField] = new Map();

		function keyIndex() {
			return indexes[keyField];
		}
		function addIndexes(indexPaths) {
			if(Array.isArray(indexPaths) == false) {
				indexPaths = [indexPaths];
			}

			for(let indexPath of indexPaths) {
				if(indexPath in indexes)
					continue;

				indexes[indexPath] = new Map();
			}
			refreshIndexes(indexPaths);
		}
		function removeIndexes(indexPaths) {
			if(Array.isArray(indexPaths) == false) {
				indexPaths = [indexPaths];
			}

			for(let indexPath of indexPaths) {
				if(indexPath == keyField)
					continue;

				indexes.delete(indexPath);
			}
		}
		function refreshIndexes(indexPaths) {
			if(indexPaths == null) { // all by default
				indexPaths = [];
				for(let indexPath in indexes) {
					indexPaths.push(indexPath);
				}
			}
			if(Array.isArray(indexPaths) == false) {
				indexPaths = [indexPaths];
			}

			for(let indexPath of indexPaths) {
				if(indexPath == keyField || indexPath in indexes == false )
					continue; // do not refresh
				indexes[indexPath] = new Map();
			}
	
			for(let object of keyIndex().values()) {
				for(let indexPath of indexPaths) {
					if(indexPath == keyField)
						continue; // always refreshed
					let index = indexes[indexPath];

					let indexKey = object[indexPath];
					let tmpList = index.get(indexKey);
					if(tmpList == null)
						tmpList = [];
					tmpList.push(object);
					index.set(indexKey, tmpList);
				}
			}
		}

		this.name = function() {
			return name;
		}
		this.keyField = function() {
			return keyField;
		}
		this.get = function(indexPath, values, negation) {
			if(indexPath in indexes == false) 
				return [];
			if(Array.isArray(values) == false) 
				values = [values];

			let objectList = [];
			for(let value of values) {
				let objects = indexes[indexPath].get(value);

				if(objects != null) {	
					if(indexPath == keyField) {
						objects = [objects];
					} 
					objectList = objectList.concat(objects);	
				}
			}
			if(negation == true) {
				let objectIds = new Set();
				for(let dummy of objectList) {
					objectIds.add(dummy.Id);
				}
				objectList = [];
				for(let object of keyIndex().values()) {
					if(objectIds.has(object.Id) == false) {
						objectList.push(object);
					}
				}
			}
			objectList = objectList.map(function(obj) { return Object.assign({}, obj); });
			return objectList;
		}
		this.save = function(objects, callback) {
			if(Array.isArray(objects) == false) {
				objects = [objects];
			}
			let updateObjects = [];
			for(let object of objects) {
				if(keyIndex().has(object[keyField])) {
					let oldObject = keyIndex().get(object[keyField]);
					oldObject = Object.assign(oldObject, object); // update only changed values
					updateObjects.push(oldObject);
				} else { // reindexing only necessary for new objects
					keyIndex().set(object[keyField], object);
					updateObjects.push(object);
				}
			}
			refreshIndexes();

			if ('indexedDB' in window == false)
				return;

			let dbRequest = window.indexedDB.open(
				database.name 
				, database.version
			); 
			dbRequest.onsuccess = function(event) {
				let db = dbRequest.result;
				let transaction = db.transaction([name], 'readwrite');
				let store = transaction.objectStore(name);
				
				for(let object of updateObjects) {
					let request = store.put(object);
					request.onerror = function(event) {
						error('Error', event.target.error.name);
					}
					request.onsuccess = function(event) {
						if(callback)
							callback();
					}
				}
			}
		}
		this.delete = function(objects, callback) {
			// reindexing necessary
			if(Array.isArray(objects) == false) {
				objects = [objects];
			}

			let deleteKeys = [];
			for(let object of objects) {
				let deleteKey;
				if(keyField in object) {
					deleteKey = object[keyField];
				} else {
					// assume that the objects themselves are the keys
					deleteKey = object; 
				}
				keyIndex().delete(deleteKey);
				deleteKeys.push(deleteKey);
			}
			refreshIndexes();

			if ('indexedDB' in window == false)
				return;

			let dbRequest = window.indexedDB.open(
				database.name 
				, database.version
			); 
			dbRequest.onsuccess = function(event) {
				let db = dbRequest.result;
				let transaction = db.transaction([name], 'readwrite');
				let store = transaction.objectStore(name);
				
				for(let key of deleteKeys) {
					let request = store.delete(key);
					request.onerror = function(event) {
						error('Error', event.target.error.name);
					}
					request.onsuccess = function(event) {
						if(callback)
							callback();
					}
				}
			}
		}
	};

	return {
		get: function(database, storeName, indexPath, value) {
			return this[database][storeName].get(indexPath, value);
		},
		save: function(database, storeName, objects, callback) {
			return this[database][storeName].save(objects, callback);
		},
		delete: function(database, storeName, objects, callback) {
			return this[database][storeName].delete(objects, callback);
		},
		storeChannel: function(channel) {
			this.messenger.passwords.save(channel);
		},

		initializeMemory: function(callback) {
			debug("initialize memory");
			if ('indexedDB' in window == false) {
				if(callback) {
					callback();
				}
				return;
			}	

			let openTransactions = 0;
			let allowCallback = false;
			function gatherForCallback(diff) {
				openTransactions += diff;
				if(openTransactions <= 0 && allowCallback) {
					if(callback) {
						callback();
					}
				}
			}
			for(let databaseName in this) {
				let database = this[databaseName];
				if(database.name == null || database.version == null)
					continue;

				gatherForCallback(1);
				let request = window.indexedDB.open(
					database.name 
					, database.version
				);
				request.onerror = function(event) {
					gatherForCallback(-1);
				}
				request.onsuccess = function(event) {
					let db = request.result;

					let asyncCount = 1;
					let allAsyncCallsAdded = false;

					let storeList = [];
					for(let storeKey in database) {
						if(database[storeKey].name != null) {
							storeList.push(database[storeKey].name());
						}
					}
					let transaction = db.transaction(storeList, 'readonly');

					for(let storeKey in database) {
						if(database[storeKey].name == null)
							continue;

						let objectStoreMemory = database[storeKey];
						gatherForCallback(1);
						let objects = [];
						let objectStore = transaction.objectStore(objectStoreMemory.name());
						objectStore.openCursor().onerror = function(event) {
							gatherForCallback(-1);
						}
						objectStore.openCursor().onsuccess = function(event) {
							let cursor = event.target.result;
							if(cursor) {
								objects.push(cursor.value);
								cursor.continue();
							} else {
								objectStoreMemory.save(objects);
								gatherForCallback(-1);
							}
						}	
					}
					gatherForCallback(-1);
				}
			}
			allowCallback = true;
			gatherForCallback(0);	
		},
		executeUpgrades: function(callback, startIndex=0) {
			if(upgrades.length <= startIndex) {
				if(callback) {
					callback();
				}
				return;
			}

			let upgrade = upgrades[startIndex];
			debug("database upgrade: ", upgrade);

			let version = ((database in this == false) 
				? 0
				: this[database].version
			) + 1;

			{ // set/update database version
				let database = this[upgrade.database];
				if(database == null) {
					database = {
						name: upgrade.database
						, version: version
					};
					this[upgrade.database] = database;
				} else {
					database.version = version;
				}
			}

			debug("prepare upgrade");
			upgrade.prepare();

			if ('indexedDB' in window == false) {
				this.executeUpgrades(callback, startIndex+1);
				return;
			}
			let request = window.indexedDB.open(upgrade.database, version);
			request.onsuccess = function(event) {
				request.result.close();
				this.executeUpgrades(callback, startIndex+1);
			}.bind(this);

			request.onupgradeneeded = function(upgrade, event) {
				debug("execute upgrade");
				upgrade.execute(event);
			}.bind(this, upgrade);
		},
		queueUpgrade: function(database, prepare, execute) {
			let upgrade = {
				database: database,
				prepare: prepare,
				execute: execute
			};
			debug("queue upgrade: ", upgrade);
			upgrades.push(upgrade);
		},
		prepareDatabases: function(callback) {
			debug("prepare databases");
			this.queueUpgrade('messenger', function() {
				if(this.messenger == null) {
					this.messenger = {};
				}
				this.messenger.passwords = new ObjectStore(
					this.messenger
					, 'passwords'
					, 'id'
				); 
			}.bind(this), function(event) {
				if ('indexedDB' in window == false)
					return;

				let db = event.target.result;
		    	db.createObjectStore(this.messenger.passwords.name(), {
		    		keyPath: this.messenger.passwords.keyField() 
		    	}); 	
			}.bind(this));

			this.executeUpgrades(callback);		
		},
		init: function(callback) {
			debug("init databases");
			if ('indexedDB' in window == false) {
				error('This browser doesn\'t support IndexedDB. Created connections and sent messages will only be available for the current session.');
			}

			this.prepareDatabases(callback);
		},
	};
})()



function getChannelData(id, callback) {
	var transaction = db.transaction([channelStoreName], 'readonly');
	var objectStore = transaction.objectStore(channelStoreName);
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
	let transaction = db.transaction([channelStoreName], 'readwrite');
	let store = transaction.objectStore(channelStoreName);
	
	let request = store.add(channel);
	request.onerror = function(e) {
		error('Error', e.target.error.name);
	};
	request.onsuccess = function(e) {
    	info('Channel stored successfully:', channel);	
    	channels.push(channel);
        authenticate([channel]);		
	};
}

//
function sendMessageRequest(from, to, message) {
	getChannelData(from, function(request) {
	    let xhttp = new XMLHttpRequest();
	    xhttp.onreadystatechange = function() {
	    	if (this.readyState == 4 && this.status == 200) {
	    		let response = JSON.parse(this.responseText);
	    	}
	    };
	    // console.log(request.result.secret, to, message);
	    xhttp.open("POST", "database/sendMessage.php", true);
		xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
		xhttp.send("from="+from+"&password="+request.result.password+"&to="+to+"&message="+message);	
	});
}


function loadFromDatabase(callback) {
	let tx = db.transaction(channelStoreName, "readonly");
	let store = tx.objectStore(channelStoreName);

	store.openCursor().onsuccess = function(event) {
		let cursor = event.target.result;
		if(cursor) {
			channels.push(cursor.value);
			cursor.continue();
		} else if(callback) {
			callback();
		}
	}	
}



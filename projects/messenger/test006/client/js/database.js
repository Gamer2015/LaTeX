let messengerDatabase = 'messenger'
let channelStoreName = 'channels'

let database = (function() {
	let upgrades = [];

	let ObjectStore = function(_database, _storeName, _keyField) {
		let database = _database;
		let name = _storeName;
		let keyField = _keyField;

		let recordsOutdated = false;
		let records = [];
		let indexes = {};
		indexes[keyField] = new Map();

		function keyIndex() {
			return indexes[keyField];
		}
		function getRecords() {
			if(recordsOutdated == true) {
				records = [];
				for(let record of keyIndex().values()) {
					records.push(record);
				}
			}
			return records;
		}

		/* indexes not supported yet
		function addIndex(indexPaths) {
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
		*/

		this.name = function() {
			return name;
		}
		this.keyField = function() {
			return keyField;
		}

		this.refresh = function(callback) {

		}
		this.get = function(restrictions) {
			let objects = getRecords();
			if(Array.isArray(restrictions) == false) 
				restrictions = [restrictions];

			let primitives = new Set(['string', 'number', 'boolean']);
			for(let restriction of restrictions) {
				if(restriction == null) {
					continue;
				}
				if(restriction.negate !== true) {
					restriction.negate = false;
				}

				if(primitives.has(typeof(restriction.values))) {
					restriction.values = [restriction.values];
				} 
				if(Array.isArray(restriction.values) == true) {
					restriction.values = new Set(restriction.values);
				}

				objects = objects.filter(function(obj) {
					return restriction.values.has(obj[restriction.field]) != restriction.negate;
				});
			}
			return objects.map(function(obj) { return Object.assign({}, obj); });
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
					records.push(object);
				}
			}
			// refreshIndexes(); - indexes not supported yet

			if ('indexedDB' in window == false)
				return;

			let gathering = (function(method) {
				let blockerCount = 0;
				let allowExecution = false;
				return {
					block: function() {
						blockerCount += 1;
					},
					execute: function() {
						blockerCount -= 1;
						if(blockerCount <= 0 && allowExecution == true) {
							if(method)
								method();
						}
					},
					allow: function() {
						allowExecution = true;
						this.block();
						this.execute();
					}
				};
			})(callback);

			gathering.block();
			let dbRequest = window.indexedDB.open(
				database.name 
				, database.version
			); 
			dbRequest.onerror = function(event) {
				error('Error', event.target.error.name);
				gathering.execute();
			}
			dbRequest.onsuccess = function(event) {
				let db = dbRequest.result;

				gathering.block();	
				let transaction = db.transaction([name], 'readwrite');
				transaction.oncomplete = function(event) {
					gathering.execute();
				}
				transaction.onerror = function(event) {
					error('Error', event.target.error.name);
					gathering.execute();
				}

				let store = transaction.objectStore(name);
				for(let object of updateObjects) {
					gathering.block();
					let request = store.put(object);
					request.onerror = function(event) {
						error('Error', event.target.error.name);
						gathering.execute();
					}
					request.onsuccess = function(event) {
						gathering.execute();
					}
				}
				gathering.execute();
			}
			gathering.allow();
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
			recordsOutdated = true;
			// refreshIndexes();

			if ('indexedDB' in window == false)
				return;

			let gathering = (function(method) {
				let blockerCount = 0;
				let allowExecution = false;
				return {
					block: function() {
						blockerCount += 1;
					},
					execute: function() {
						blockerCount -= 1;
						if(blockerCount <= 0 && allowExecution == true) {
							if(method)
								method();
						}
					},
					allow: function() {
						allowExecution = true;
						this.block();
						this.execute();
					}
				};
			})(callback);

			gathering.block();
			let dbRequest = window.indexedDB.open(
				database.name 
				, database.version
			); 
			dbRequest.onerror = function(event) {
				error('Error', event.target.error.name);
				gathering.execute();
			}
			dbRequest.onsuccess = function(event) {
				let db = dbRequest.result;
				gathering.block();
				let transaction = db.transaction([this.name()], 'readwrite');
				transaction.oncomplete = function(event) {
					gathering.execute();
				}
				transaction.onerror = function(event) {
					error('Error', event.target.error.name);
					gathering.execute();
				}

				let store = transaction.objectStore(this.name());
				for(let key of deleteKeys) {
					gathering.block();
					let request = store.delete(key);
					request.onerror = function(event) {
						error('Error', event.target.error.name);
						gathering.execute();
					}
					request.onsuccess = function(event) {
						gathering.execute();
					}
				}
				gathering.execute();
			}
			gathering.allow();
		}
	};

	return {
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
						let cursor = objectStore.openCursor();
						cursor.onerror = function(event) {
							gatherForCallback(-1);
						}
						cursor.onsuccess = function(event) {
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
			debug("database upgrade: ", upgrade.database, upgrade.name);

			let version = 1;
			{ // set/update database version
				let database = this[upgrade.database];
				version += (database ? database.version : 0);

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

			info("upgrade metadata: ", upgrade.metadata);	
			if(upgrade.metadata) {
				upgrade.metadata();
			}

			if ('indexedDB' in window == false) {
				info("clean up: ", upgrade.cleanUp);
				if(upgrade.cleanUp) {
					upgrade.cleanUp();
				}
				this.executeUpgrades(callback, startIndex+1);
				return;
			}

			let request = window.indexedDB.open(upgrade.database, version);
			request.onupgradeneeded = function(upgrade, event) {
				info("upgrade stores: ", upgrade.stores);		
				if(upgrade.stores) {
					upgrade.stores(event);
				}
			}.bind(this, upgrade);

			request.onerror = function(event) {
				// probably version error due to our upgrade framework
				if(event.target.error.name === 'VersionError') {
					// ignore version errors
					// update has most likely already been done in this case
					// skip directly to next upgrade
					this.executeUpgrades(callback, startIndex+1);				
				} else {
					// abort, something went terribly wrong
					error('Error', event.target.error.name);
				}
			}.bind(this);

			request.onsuccess = function(upgrade, event) {
				let finish = function() {
					request.result.close();
					this.executeUpgrades(callback, startIndex+1);
				}.bind(this);

				info("update records: ", upgrade.records);	
				if(upgrade.records) {
					upgrade.records(request.result, function() {
						finish();
					}.bind(this));
				} else {
					finish();	
				}
			}.bind(this, upgrade);
		},
		queueUpgrade: function(name, database, metadata, stores, records) {
			// preperation and cleanup also have to happen for memory-only instances
			let upgrade = {
				name: name,
				database: database,
				metadata: metadata,
				stores: stores,
				records: records
			};
			debug("queue upgrade: ", upgrade);
			upgrades.push(upgrade);
		},
		prepareDatabases: function(callback) {
			debug("prepare databases"); 

			this.queueUpgrade(
				'2020-12-10 (1): create password store'
				,'messenger'
				, function metadata() {
					if(this.messenger == null) {
						this.messenger = {};
					}
					this.messenger.passwords = new ObjectStore(
						this.messenger
						, 'passwords'
						, 'id'
					); 
				}.bind(this), function stores(event) {
					let db = event.target.result;
			    	db.createObjectStore(this.messenger.passwords.name(), {
			    		keyPath: this.messenger.passwords.keyField() 
			    	}); 	
			}.bind(this));

			this.queueUpgrade(
				'2020-12-12 (1): create accounts store and save passwords there'
				, 'messenger'
				, function metadata() {
					if(this.messenger == null) {
						this.messenger = {};
					}
					this.messenger.accounts = new ObjectStore(
						this.messenger
						, 'accounts'
						, 'id'
					); 
				}.bind(this), function stores(event) {
					let db = event.target.result;
			    	db.createObjectStore(this.messenger.accounts.name(), {
			    		keyPath: this.messenger.accounts.keyField() 
			    	});
				}.bind(this), function records(database, callback) {
					let transaction = database.transaction([
						this.messenger.accounts.name()
						, this.messenger.passwords.name()
					], 'readwrite');

					let passwordStore = transaction.objectStore(this.messenger.passwords.name());
					let accountStore = transaction.objectStore(this.messenger.accounts.name());
					
					let cursor = passwordStore.openCursor();
					cursor.onerror = function(event) {
						error('Error', event.target.error.name);
					}
					cursor.onsuccess = function(event) {
						let cursor = event.target.result;
						if(cursor) {
							accountStore.put(object);
							cursor.continue();
						} else {
							if(callback) {
								callback();
							}
						}
					}	
			}.bind(this));

			this.queueUpgrade(
				'2020-12-12 (2): delete passwords store 1'
				, 'messenger'
				, null
				, function stores(event) {
					let db = event.target.result;
					db.deleteObjectStore(this.messenger.passwords.name());
				}.bind(this));

			this.queueUpgrade(
				'2020-12-12 (3): delete passwords store 2'
				, 'messenger'
				, function metadata(callback) {
					delete this.messenger["passwords"];
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



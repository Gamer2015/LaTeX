(function() {
	window.memoryStorage = {};

	function isEmpty(o) {
		for (let i in o) {
	  		return false;
	 	}
	 	return true;
	};

	if (isEmpty(memoryStorage)) {
		// Ask other tabs for memoryStorage
		localStorage.setItem('getSessionStorage', Date.now());
	};

	window.addEventListener('storage', function(event) {

		//console.log('storage event', event);

		if (event.key == 'getSessionStorage') {
			// Some tab asked for the memoryStorage -> send it

			localStorage.setItem('sessionStorage', JSON.stringify(memoryStorage));
			localStorage.removeItem('sessionStorage');

		} else if (event.key == 'sessionStorage' && isEmpty(memoryStorage)) {
			// sessionStorage is empty -> fill it

			let data = JSON.parse(event.newValue),
						value;

			for (key in data) {
				memoryStorage[key] = data[key];
			}

			showSessionStorage();
		}
	});

	window.onbeforeunload = function() {
		sessionStorage.clear();
	};
})();

function storeAccounts(updatedAccounts) {
	let storedAccounts = {};
	try {
		storedAccounts = JSON.parse(sessionStorage.getItem('accounts'));
	} catch(err) {}
	if(storedAccounts == null) {
		storedAccounts = {};
	}

	for(let account of updatedAccounts) {
		storedAccounts[account.username] = account;

		// set some default values if not already done so
		if(account.password == null) {
			account.password = calculatePassword(account.secret);
		}
		if(account.key == null) {
			account.key = calculateAccountKey(account.secret);
		}
	}

	sessionStorage.setItem('accounts', JSON.stringify(storedAccounts));
}

function getAccounts(usernames) {
	let storedAccounts = {};
	try {
		storedAccounts = JSON.parse(sessionStorage.getItem('accounts'));
	} catch(err) {}
	if(storedAccounts == null) {
		storedAccounts = {};
	}
	
	if(usernames==true) {
		return storedAccounts;
	} 

	let tmpMap = {}
	for(let username of usernames) {
		tmpMap[username] = storedAccounts[username];
	}

	return tmpMap;
}

function logout(usernames) {
	let storedAccounts = {};
	try {
		storedAccounts = JSON.parse(sessionStorage.getItem('accounts'));
	} catch(err) {}
	if(storedAccounts == null) {
		storedAccounts = {};
	}

	if(usernames == true) {
		storedAccounts = {};
	} else {
		for(let username of usernames) {
			delete storedAccounts[username];
		}
	}

	sessionStorage.setItem('accounts', JSON.stringify(storedAccounts));
}

function setCurrentAccount(username) {
	let storedAccounts = JSON.parse(sessionStorage.getItem('accounts'));
	if(storedAccounts == null) {
		storedAccounts = {};
	}

	sessionStorage.setItem('account', JSON.stringify(storedAccounts[username]));
}


function getCurrentAccount() {
	return JSON.parse(sessionStorage.getItem('account'));
}


/*
let packages = {}

let memory = {};
function initializeDatabase(callback) {
	debug("init databases");	
	if ('indexedDB' in window == false) {
		error('This browser doesn\'t support IndexedDB. All data will be lost after closing the browser.');
		return
	}

	info("upgrade database")
	let databases = {};
	function executeUpgrades(callback, startIndex=0) {
		info("executeUpgrades", startIndex, upgrades.length);
		if(upgrades.length <= startIndex) {
			if(callback) {
				callback();
			}
			return;
		}
		upgrade = upgrades[startIndex];
		let database = null;
		{
			database = databases[upgrade.database];
			if(database == null) {
				database = {
					version: 0
				};
				databases[upgrade.database] = database;
			}
			database.version += 1;
		}

		info("request", upgrade.database, database.version);
		let request = window.indexedDB.open(upgrade.database, database.version);	
		request.onupgradeneeded = function(event) {
			info("upgrade database: ", upgrade.database);		
			if(upgrade.upgrade) {
				upgrade.upgrade(event.target.result);
			}
		}

		request.onerror = function(event) {
			// probably version error due to our upgrade framework
			if(event.target.error.name === 'VersionError') {
				// ignore version errors
				// update has most likely already been done in this case
				// skip directly to next upgrade
				executeUpgrades(callback, startIndex+1);				
			} else {
				// abort, something went terribly wrong
				error('Error', event.target.error.name);
			}
		};

		request.onsuccess = function(event) {
			info("update records: ", upgrade.records);	
			if(upgrade.success) {
				upgrade.success(request.result, function() {
					request.result.close();
					executeUpgrades(callback, startIndex+1);
				});
			} else {
				request.result.close();
				executeUpgrades(callback, startIndex+1);
			}
		}
	}

	let upgrades = [{
		date: '2020-12-22'
		, author: 'stefan kreiner'
		, summary: 'create provider database and account store'
		, database: 'database'
		, upgrade: function(database) {
	    	let accountStore = database.createObjectStore('accounts', { keyPath: 'username' }); 
		}, success: function(database, callback) {
			if(callback) {
				callback();
			}
		}
	}, {
		date: '2020-12-22'
		, author: 'stefan kreiner'
		, summary: 'create package store'
		, database: 'database'
		, upgrade: function(database) {
			database.createObjectStore('packages', { keyPath: ['username', 'id'] });  
		}, success: function(database, callback) {
			if(callback) {
				callback();
			}
		}
	}];
	executeUpgrades(callback)
}
*/


/*let database = (function() {
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

		this.addIndex = function(indexPaths) {
			if(Array.isArray(indexPaths) == false) {
				indexPaths = [indexPaths];
			}
			let indexName = indexPaths.join('.');
			if(indexName in indexes == false) {
				indexes[indexName] = new Map();
				refreshIndexes(indexPaths);
			}
		}
		this.removeIndexes = function(indexNames) {
			if(Array.isArray(indexNames) == false) {
				indexNames = [indexNames];
			}

			for(let indexName of indexNames) {
				if(indexName == keyField)
					continue;

				indexes.delete(indexName);
			}
		}
		function refreshIndexes(indexNames) {
			if(indexNames == null) { // all by default
				indexNames = [];
				for(let indexName in indexes) {
					indexNames.push(indexName);
				}
			}
			if(Array.isArray(indexNames) == false) {
				indexNames = [indexNames];
			}

			// reset
			for(let indexName of indexNames) {
				if(indexName == keyField || indexName in indexes == false )
					continue; // do not refresh
				indexes[indexName] = new Map();
			}
	
			for(let object of keyIndex().values()) {
				for(let indexName of indexNames) {
					if(indexName == keyField)
						continue; // always refreshed

					let index = indexes[indexName];

					let fields = indexName.split('.');
					for(let i = 0; i < fields.length; ++i) {
						let field = fields[i];
						let indexKey = object[field];
						let dummy = index.get(indexKey);
						if(dummy == null) {
							if(i + 1 == fields.length) {
								dummy = [];	
							} else {
								dummy = new Map();
							}
						}
						if(i + 1 == fields.length) {
							dummy.push(object);
						}
						index.set(indexKey, dummy);
						index = dummy;
					}
				}
			}
		}

		this.name = function() {
			return name;
		}
		this.keyField = function() {
			return keyField;
		}

		this.get = function(restrictions) {
			if(Array.isArray(restrictions) == false) {
				restrictions = [restrictions].filter(function(obj) { 
					return obj != null; 
				});
			}

			let primitives = new Set(['string', 'number', 'boolean']);
			restrictions = restrictions.map(function(restriction) {
				if(primitives.has(typeof(restriction))) {
					restriction = {
						values: restriction
					};
				}
				if(restriction.negate !== true) {
					restriction.negate = false;
				}
				if(restriction.field == null) {
					restriction.field = keyField;
				}

				if(primitives.has(typeof(restriction.values))) {
					restriction.values = [restriction.values];
				} 
				if(Array.isArray(restriction.values) == true) {
					restriction.values = new Set(restriction.values);
				}
				return restriction;
			})

			let bestIndex = null;
			let indexDepth = 0;
			let indexLevels = restrictions.map(function(obj) { return obj.field; });
			for(let depth = indexLevels.length; depth > 0; --depth) {
				let dummyIndex = indexLevels.join('.');
				if(dummyIndex in indexes) {
					bestIndex = dummyIndex;
					indexDepth = depth;
					break;
				}
				indexLevels.pop();
			}

			let objects = [];
			if(bestIndex != null) {
				let dummyIndexes = [indexes[bestIndex]];

				for(let i = 0; i < indexDepth; ++i) {
					let newDummyIndexes = [];
					if(restrictions[i].negate == false) {
						debug(restrictions[i].values);
						for(let value of restrictions[i].values) {
							for(let index of dummyIndexes) {
								newDummyIndexes.push(index.get(value));
							}
						}
					} else {
						for(let index of dummyIndexes) {
							for(let (value, dummy) in index) {
								if(restrictions[i].values.has(value) == false) {
									newDummyIndexes.push(dummy);
								}
							}
						}
					}
					dummyIndexes = newDummyIndexes;
				}
				objects = dummyIndexes.reduce(function(total, current) {
					try {
						// try if last index is array
						total = total.concat(current);
					} catch(err) {
						// try if last index must return a single element
						total.push(current);
					}
					return total;
				}, []);
				// query by indexes not yet supported
			} else {
				objects = getRecords();
			}

			for(let i = indexDepth; i < restrictions.length; ++i) {
				let restriction = restrictions[i];
				objects = objects.filter(function(object) {
					return restriction.values.has(object[restriction.field]) != restriction.negate;
				});
			}
			return objects.map(function(obj) { return Object.assign({}, obj); });
		}
		this.save = function(objects, callback, commit=true) {
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

			if ('indexedDB' in window == false || commit == false)
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
		this.delete = function(objects, callback, commit=true) {
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
				if(keyIndex().has(deleteKey)) {
					keyIndex().delete(deleteKey);
					deleteKeys.push(deleteKey);
					recordsOutdated = true;
				}
			}
			// refreshIndexes();

			if ('indexedDB' in window == false || commit == false)
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

			for(let databaseName in this) {
				let database = this[databaseName];
				if(database.name == null || database.version == null)
					continue;

				gathering.block();
				let request = window.indexedDB.open(
					database.name 
					, database.version
				);
				request.onerror = function(event) {
					gathering.execute();
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
						gathering.block();
						let objects = [];
						let objectStore = transaction.objectStore(objectStoreMemory.name());
						let cursor = objectStore.openCursor();
						cursor.onerror = function(event) {
							gathering.execute();
						}
						cursor.onsuccess = function(event) {
							let cursor = event.target.result;
							if(cursor) {
								objects.push(cursor.value);
								cursor.continue();
							} else {
								objectStoreMemory.save(objects, null, false);
								gathering.execute();
							}
						}	
					}
					gathering.execute();
				}
			}
			gathering.allow();	
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
*/

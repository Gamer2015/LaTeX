def forceIterable(entities):
    if isinstance(entities, set):
        return entities
    if isinstance(entities, list):
        return entities

    try:
        if(isinstance(entities, str)):
            # do not consider strings as list of characters
            raise Exception

        if(isinstance(entities, object)):
            # do not consider objects as set of (key,value)-pairs
            raise Exception

        for entity in entities:
            break
    except:
        entities = list([entities])
    return entities

def forceSet(entities):
    if isinstance(entities, set):
        return entities

    try:
        if(isinstance(entities, str)):
            # do not consider strings as list of characters
            raise Exception
        if(isinstance(entities, object) and isinstance(entities, list) == False):
            # do not consider objects as set of (key,value)-pairs
            raise Exception
        entities = set(entities)    
    except:
        entities = set([entities])
    return entities

def forceList(entities):
    if isinstance(entities, list):
        return entities

    try:
        if(isinstance(entities, str)):
            # do not consider strings as list of characters
            raise Exception
        if(isinstance(entities, object) and isinstance(entities, set) == False):
            # do not consider objects as set of (key,value)-pairs
            raise Exception
        entities = list(entities)
    except:
        entities = list([entities])
    return entities


def shallowCopy(entity, fields):
    fields = forceSet(fields)

    tmp = {}
    for field in fields:
        if field in entity:
            tmp[field] = entity[field] 
    return tmp

def hex2bytes(entity, fields):
    fields = forceSet(fields)

    for field in fields:
        if field in entity:
            value = entity[field]
            if passisinstance(value, list) or isinstance(value, set):
                for i in range(len(value)):
                    value[i] = bytes.fromhex(value[i])
            else:
                entity[field] = bytes.fromhex(value)
    return entity
def bytes2hex(entity, fields):
    fields = forceSet(fields)

    for field in fields:
        if field in entity:
            value = entity[field]
            if passisinstance(value, list) or isinstance(value, set):
                for i in range(len(value)):
                    value[i] = value[i].hex()
            else:
                entity[field] = value.hex()
    return entity

def unpackAccount(account):
    tmp = shallowCopy(account, ["id", "username", "password", "timestamp"])
    return hex2bytes(tmp, ["id"])
def unpackAccounts(accounts):
    accounts = forceIterable(accounts)
    return [unpackAccount(account) for account in accounts]

def packAccount(account, excludes=None):
    excludes = forceSet(excludes)
    return shallowCopy(account, set(["username"]) - excludes)
def packAccounts(accounts, excludes=None):
    accounts = forceIterable(accounts)
    return [packAccount(account, excludes) for account in accounts]

def unpackPackage(package):
    tmp = shallowCopy(package, ["username", "id", "data", "key"])
    return hex2bytes(tmp, ["id"])
def unpackPackages(packages):
    packages = forceIterable(packages)
    return [unpackPackage(package) for package in packages]

def packPackage(package, excludes=None):
    excludes = forceSet(excludes)
    tmp = shallowCopy(package, set(["username", "id", "data", "key"]) - excludes)
    return bytes2hex(tmp, set(["id"]) - excludes)
def packPackages(packages, excludes=None):
    packages = forceIterable(packages)
    return [packPackage(package, excludes) for package in packages]

def packIdentity(identity, excludes):
    excludes = forceSet(excludes)
    tmp = shallowCopy(package, set(["username", "id"]) - excludes)
    return bytes2hex(tmp, set(["id"]) - excludes)
def packIdentities(identities, excludes=None):
    identities = forceIterable(identities)
    return [packIdentity(identity) for identity in identities]

def unpackMessage(message, excludes):
    excludes = forceSet(excludes)
    tmp = shallowCopy(message, set(["id", "senderId", "recipientIds", "body", "expires"]) - excludes)
    return bytes2hex(tmp, set(["id", "senderId", "recipientIds"]) - excludes)
def unpackMessages(messages, excludes=None):
    messages = forceIterable(messages)
    return [unpackMessage(message) for message in messages]

def packMessage(message, excludes):
    excludes = forceSet(excludes)
    tmp = shallowCopy(message, set(["id", "senderId", "recipientId", "body", "timestamp", "expires"]) - excludes)
    return bytes2hex(tmp, set(["id", "senderId", "recipientId"]) - excludes)
def packMessages(messages, excludes=None):
    messages = forceIterable(messages)
    return [packIdentity(message) for message in messages]

def packStatusWrapper(wrapper, entityPacker, excludes=None):
    tmp = shallowCopy(wrapper, set(["status, reason, entity"]))
    tmp["entity"] = entityPacker(tmp["entity"], excludes)
    return tmp
def packStatusWrappers(wrappers, entityPacker, excludes=None):
    wrappers = forceIterable(wrappers)
    return [
        packStatusWrapper(wrapper, entityPacker, excludes) for wrapper in wrappers
    ]


"""
    
def dbBinary2hex(dbBinary):
  return dbBinary[::-1].hex()

def fn(data):
	channels = data["channels"];
	for channel in channels:
		channel["id"] = bytes.fromhex(channel["id"])

data = {'channels':[{'id':'01234567'}]}
print(data);
fn(data)
print(data);


import secrets
import bcrypt
idLength = 8"""
#id = bytes.fromhex('000000001')  

#print(id)
#print(id.hex().lstrip('00'))
#print(dbBinary2hex(id))

"""
count = []
for i in range(100000):
	id =  secrets.token_bytes(idLength)	
	count = 1
	while id[0] == 0:
		print(id)
		id =  secrets.token_bytes(idLength)
		count = count+1

	if(count > 1):
		print(i, count)"""
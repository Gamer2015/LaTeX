def forceIterable(entities):
    if isinstance(entities, set):
        return entities
    if isinstance(entities, list):
        return entities

    try:
        if(isinstance(entities, str)):
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
            raise Exception
        if(isinstance(entities, object) and isinstance(entities, list) == False):
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
            raise Exception
        if(isinstance(entities, object) and isinstance(entities, set) == False):
            raise Exception
        entities = list(entities)
    except:
        entities = list([entities])
    return entities

def unpack(entities, fields):
    entities = forceIterable(entities)
    fields = forceSet(fields)

    tmps = []
    for entity in entities:
        tmp = {}
        for field in fields:
            if field in entity:
                tmp[field] = entity[field] 
        tmps.append(tmp)
    return tmps

def packBlobs(blobs):
    blobs = forceIterable(blobs)

    return [blob.hex() for blob in blobs]

def hex2bytes(entities, fields):
    entities = forceIterable(entities)
    fields = forceSet(fields)

    for entity in entities:
        for field in fields:
            if field in entity:
                entity[field] = bytes.fromhex(entity[field])
    return entities
def bytes2hex(entities, fields):
    entities = forceIterable(entities)
    fields = forceSet(fields)

    for entity in entities:
        for field in fields:
            if field in entity:
                entity[field] = entity[field].hex()
    return entities

def unpackAccounts(accounts):
    accounts = unpack(accounts, ["id", "password", "timestamp"])
    return hex2bytes(accounts, ["id"])

def packAccounts(accounts, excludes=None):
    if excludes == None:
        excludes = []
    excludes = forceSet(excludes)

    tmps = unpack(accounts, [
        prop for prop in ["id"] if prop not in excludes
    ])
    return bytes2hex(tmps, [
        prop for prop in ["id"] if prop not in excludes
    ])

def unpackPackages(packages):
    tmps = unpack(packages, ["accountId", "id", "data"])
    return hex2bytes(tmps, ["accountId", "id"])

def packPackages(packages, excludes=None):
    print(excludes)
    if excludes == None:
        excludes = []
    excludes = forceSet(excludes)

    tmps = unpack(packages, [
        prop for prop in ["accountId", "id", "data"] if prop not in excludes
    ])
    return bytes2hex(tmps, [
        prop for prop in ["accountId", "id"] if prop not in excludes
    ])

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
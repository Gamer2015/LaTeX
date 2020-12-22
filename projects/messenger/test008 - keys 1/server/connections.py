entityId2client = {}
client2entityIds = {}

def verify(client, entityId):
	return getClient(entityId) == client


def activeEntities():
	return len(entityId2client.keys())

def activeClients():
	return len(client2entityIds.keys())

def getClient(entityId):
	try:
		return entityId2client[entityId]
	except:
		return None

def getEntities(client):
	try:
		return client2entityIds[client]
	except:
		return []

def anyActive(entities):
	return any([entity["id"] in entityId2client for entity in entities])

"""def activeSession(entities):
	# exactly the same entities are active on a different client
	channelIds = [entity["id"] for entity in entities]
	clients = set([entityId2client[entityId] for entityId in channelIds])

	sameActiveSession = True
	if(all([entityId in entityId2client for entityId in channelIds]) == false) or len(clients) != 1:
		return false

	for client in clients:
		return set(client2entityIds[client]) == set(channelIds)"""

def remember(client, entities):
	try:
		clientEntityIds = client2entityIds[client]
	except:
		clientEntityIds = []
	clientEntityIds = [*clientEntityIds, *[entity["id"] for entity in entities]]
	client2entityIds[client] = clientEntityIds

	for entity in entities:
		entityId2client[entity["id"]] = client

def forget(client):
	try:
		clientEntityIds = client2entityIds[client]
	except:
		clientEntityIds = []
	for entityId in clientEntityIds:
		entityId2client.pop(entityId, None)

	client2entityIds.pop(client, None)

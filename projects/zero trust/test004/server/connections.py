import utilities

accountId2clients = {}
client2accountIds = {}

def verify(client, accountId):
	return client in getClients(accountId)

def activeEntities():
	return len(accountId2clients.keys())
def activeClients():
	return client2accountIds

def getClients(accountIds):
	tmpClient2accountIds = {}
	for accountId in accountIds:
		try:
			accountClients = accountId2clients[accountId]
		except:
			accountClients = set()

		for client in accountClients:
			try: 
				clientAccountIds = tmpClient2accountIds[client]
			except:
				clientAccountIds = set()
			clientAccountIds.add(accountId)
			tmpClient2accountIds[client] = clientAccountIds
	return tmpClient2accountIds

def getAccountIds(client):
	try:
		return client2accountIds[client]
	except:
		return set()

def anyActive(accounts):
	if isinstance(accounts, list) == False:
		accounts = [accounts]
	return any([account["id"] in accountId2clients for account in accounts])

"""def activeSession(entities):
	# exactly the same entities are active on a different client
	channelIds = [entity["id"] for entity in entities]
	clients = set([accountId2clients[accountId] for accountId in channelIds])

	sameActiveSession = True
	if(all([accountId in accountId2clients for accountId in channelIds]) == false) or len(clients) != 1:
		return false

	for client in clients:
		return set(client2accountIds[client]) == set(channelIds)"""

def remember(client, accountIds):
	accountIds = utilities.forceSet(accountIds);
	try:
		clientAccountIds = client2accountIds[client]
	except:
		clientAccountIds = set()
	clientAccountIds.update(accountIds)
	client2accountIds[client] = clientAccountIds
	for accountId in accountIds:
		try:
			clients = accountId2clients[accountId]
		except:
			clients = set()
		clients.add(client)
		accountId2clients[accountId] = clients
	print("clientsByAccountId", accountId2clients)

def forget(client):
	try:
		clientAccountIds = client2accountIds[client]
	except:
		clientAccountIds = set()
	for accountId in clientAccountIds:
		accountId2clients[accountId].discard(client)
		if len(accountId2clients[accountId]) == 0:
			accountId2clients.pop(accountId, None)
	client2accountIds.pop(client, None)

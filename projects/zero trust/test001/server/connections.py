accountId2clients = {}
client2accountIds = {}

def verify(client, accountId):
	return client in getClients(accountId)

def activeEntities():
	return len(accountId2clients.keys())
def activeClients():
	return len(client2accountIds.keys())

def getClients(accountId):
	try:
		return accountId2clients[accountId]
	except:
		return set()

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

def remember(client, accounts):
	if isinstance(accounts, list) == False:
		accounts = [accounts]
	try:
		clientAccountIds = client2accountIds[client]
	except:
		clientAccountIds = set()
	clientAccountIds.update([account["id"] for account in accounts])
	client2accountIds[client] = clientAccountIds
	for account in accounts:
		try:
			clients = accountId2clients[account["id"]]
		except:
			clients = set()
		clients.add(client)
		accountId2clients[account["id"]] = clients

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

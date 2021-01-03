import utilities

username2clients = {}
client2usernames = {}

def verify(client, accountId):
	return client in getClients(accountId)

def activeUsernames():
	return username2clients
def activeClients():
	return client2usernames

def getClients(usernames):
	tmpClient2usernames = {}
	for username in usernames:
		try:
			accountClients = username2clients[username]
		except:
			accountClients = set()

		for client in accountClients:
			try: 
				clientUsernames = tmpClient2usernames[client]
			except:
				clientUsernames = set()
			clientUsernames.add(username)
			tmpClient2usernames[client] = clientUsernames
	return tmpClient2usernames

def getUsernames(client):
	try:
		return client2usernames[client]
	except:
		return set()

def anyActive(accounts):
	if isinstance(accounts, list) == False:
		accounts = [accounts]
	return any([account["id"] in username2clients for account in accounts])

"""def activeSession(entities):
	# exactly the same entities are active on a different client
	channelIds = [entity["id"] for entity in entities]
	clients = set([username2clients[accountId] for accountId in channelIds])

	sameActiveSession = True
	if(all([accountId in username2clients for accountId in channelIds]) == false) or len(clients) != 1:
		return false

	for client in clients:
		return set(client2usernames[client]) == set(channelIds)"""

def remember(client, usernames):
	usernames = utilities.forceSet(usernames);
	try:
		clientUsernames = client2usernames[client]
	except:
		clientUsernames = set()
	clientUsernames.update(usernames)
	client2usernames[client] = clientUsernames
	for username in usernames:
		try:
			clients = username2clients[username]
		except:
			clients = set()
		clients.add(client)
		username2clients[username] = clients

def forget(client):
	try:
		clientUsernames = client2usernames[client]
	except:
		clientUsernames = set()
	for username in clientUsernames:
		username2clients[username].discard(client)
		if len(username2clients[username]) == 0:
			username2clients.pop(username, None)
	client2usernames.pop(client, None)

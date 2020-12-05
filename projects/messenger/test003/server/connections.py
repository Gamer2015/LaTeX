channelId2client = {}
client2channelIds = {}

def activeChannels():
	return len(channelId2client.keys())

def activeClients():
	return len(client2channelIds.keys())

def getClient(channelId):
	try:
		return channelId2client[channelId]
	except:
		return None

def getChannels(websocket):
	try:
		return client2channelIds[websocket]
	except:
		return []

def anyActive(channels):
	return any([channel["id"] in channelId2client for channel in channels])

def remember(websocket, channels):
	try:
		allClientChannels = client2channelIds[websocket]
	except:
		allClientChannels = []
	allClientChannels = [*allClientChannels, *[channel["id"] for channel in channels]]
	client2channelIds[websocket] = allClientChannels

	for channel in channels:
		channelId2client[channel["id"]] = websocket

def forget(websocket):
	try:
		allClientChannels = client2channelIds[websocket]
	except:
		allClientChannels = []
	for channelId in allClientChannels:
		channelId2client.pop(channelId, None)

	client2channelIds.pop(websocket, None)

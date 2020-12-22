# security
import secrets

# utility
import json 
import copy 

requests = {}

def generateRequestId():
	requestTokenLength = 8
	requestId = secrets.token_bytes(requestTokenLength).hex()
	while requestId in requests:
		requestId = secrets.token_bytes(requestTokenLength).hex()
	return requestId	

async def send(websocket, subject, message, verifyConfirmation=False):
	message["header"] = {
		"subject": subject
	}
	if verifyConfirmation == True:
		message["header"]["id"] = generateRequestId()
		requests[message["header"]["id"]] = message

		message = copy.deepcopy(message)
		if "behavior" in message:
			del message["behavior"]

	await websocket.send(json.dumps(message))

async def respond(websocket, message, response, verifyConfirmation=False):
	await send(websocket, 'response', {
		'responseTo' : message["header"]["id"]
		, **response
	}, verifyConfirmation)

async def acknowledge(websocket, message):
	await send(websocket, 'acknowledge', {
		'responseTo' : message["header"]["id"]
	}, False)
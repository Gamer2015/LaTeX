# utility
import json 

requests = {}

def generateRequestId():
	requestTokenLength = 8
	requestId = secrets.token_bytes(requestTokenLength).hex()
	while requestId in requests:
		requestId = secrets.token_bytes(requestTokenLength).hex()
	return requestId	

async def send(websocket, subject, message, verifyConfirmation=False):
	message["subject"] = subject
	if verifyConfirmation == True:
		message["id"] = generateRequestId()
		requests[message["id"]] = message

		message = copy.deepcopy(message)
		del request["behavior"]

	await websocket.send(json.dumps(message))

async def respond(websocket, request, response, verifyConfirmation=False):
	await send(websocket, 'response', {
		'responseTo' : request["id"]
		, **response
	}, verifyConfirmation)

async def acknowledge(websocket, request):
	await send(websocket, 'acknowledge', {
		'responseTo' : request["id"]
	}, False)
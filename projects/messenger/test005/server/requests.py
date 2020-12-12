# utility
import json 

requests = {}

def generateRequestId():
    requestTokenLength = 8
    requestId = secrets.token_bytes(requestTokenLength).hex()
    while requestId in requests:
    	requestId = secrets.token_bytes(requestTokenLength).hex()
    return requestId	

async def send(websocket, request, needResponse=False):
	if needResponse == True:
		requestId = generateRequestId()
		request["requestId"] = requestId
		requests[requestId] = request

	print(request)
	await websocket.send(json.dumps(request))

async def respond(websocket, responseTo, request, needResponse=False):
    await send(websocket, {
        'message': 'response'
        , 'responseTo' : responseTo
        , **request
	}, needResponse)
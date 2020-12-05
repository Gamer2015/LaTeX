#!/usr/bin/env python

# WS server example that synchronizes state across clients
import logging
logging.basicConfig(level=logging.DEBUG)

import asyncio
import json
import websockets
import functools 
import database


async def createChannel(websocket, dbFileName, data):
	requestToken = data["requestToken"]
	logging.debug("data: %s", data);
	password = data["password"]
	id = database.createChannel(dbFileName, password)
	if id == None:
		await websocket.send(json.dumps({ 
			'message' : 'response',
			'requestToken' : requestToken,
			'status': 'failed', 
		}));	
	else:
		await websocket.send(json.dumps({ 
			'message' : 'response', 
			'requestToken' : requestToken,
			'status': 'success', 
			'id': id.hex()
		}))



clients = set()
async def register(websocket):
	clients.add(websocket)
async def unregister(websocket):
	clients.remove(websocket)
async def counter(websocket, path, dbFileName):
	# register(websocket) sends user_event() to websocket
	await register(websocket)
	openRequestTokens = set()	
	try:
		async for message in websocket:
			data = json.loads(message)
			logging.debug("%s, %s", data, path)

			requestToken = data["requestToken"];
			if requestToken in openRequestTokens:
				# request token collision or request has already been added to the list
				# please try again with a different request token or don't bother, we already got the message
				websocket.send(json.dumps({ 'message': 'collision', 'requestToken' : requestToken}));
				continue
			else:
				openRequestTokens.add(requestToken)
				
			if data["message"] == "create channel":
				await createChannel(websocket, dbFileName, data)
			openRequestTokens.remove(requestToken)
	finally:
		await unregister(websocket)

def init(server, port, dbFileName):
	start_server = websockets.serve(functools.partial(counter,dbFileName=dbFileName), server, port)

	asyncio.get_event_loop().run_until_complete(start_server)
	asyncio.get_event_loop().run_forever()

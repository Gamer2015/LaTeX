#!/usr/bin/env python

# WS server example that synchronizes state across clients
import logging
logging.basicConfig(level=logging.DEBUG)

import asyncio
import json
import websockets
import functools 
import database
import connections

async def respond(websocket, data, response):
    await websocket.send(json.dumps({ 
            'message' : 'response', 
            'requestToken' : data["requestToken"],
            **response
        }))

async def createChannel(websocket, dbFileName, data):
    password = data["password"]
    id = database.createChannel(dbFileName, password)
    if id == None:
        await respond(websocket, data, {'status': 'failed'});
    else:
        await respond(websocket, data, {
            'status': 'success', 
            'id': id.hex()
        });

async def authenticate(websocket, dbFileName, data):
    channels = data["channels"];
    for channel in channels:
        channel["id"] = bytes.fromhex(channel["id"])

    authInformation = database.authenticate(dbFileName, channels)
    success = all([info["authSuccess"] for info in authInformation])
    #activeSession = connections.activeSession(channels)
    anyActive = connections.anyActive(channels)
    # more flexibility possible, but good enough for now
    if success == False or anyActive == True:
        await respond(websocket, data, {'status': 'failed'}); 
    else:
        connections.remember(websocket, data["channels"])
        await respond(websocket, data, {'status': 'success'});  
    return success

async def counter(websocket, path, dbFileName):
    # register(websocket) sends user_event() to websocket
    #await register(websocket)
    openRequestTokens = set()   
    authenticatedChannelIds = set()
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
            elif data["message"] == "authenticate":
                await authenticate(websocket, dbFileName, data)
                logging.debug("auth channels total: %i, auth clients total: %i", connections.activeChannels(), connections.activeClients())

            openRequestTokens.remove(requestToken)
    finally:
        connections.forget(websocket)

def init(server, port, dbFileName):
    start_server = websockets.serve(functools.partial(counter,dbFileName=dbFileName), server, port)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

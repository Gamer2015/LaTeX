#!/usr/bin/env python

# logging is important
import logging
logging.basicConfig(level=logging.DEBUG)

# server
import asyncio
import websockets
import functools

# utility
import json 
import database
import connections
import requests

# communication
import secrets


async def respond(websocket, data, response):
    response = { 
        'message' : 'response', 
        'responseTo' : data["requestId"],
        'requestId' : generateRequestId(),
        **response
    }
    print(response)
    await websocket.send(json.dumps(response))

async def sendMessage(websocket, dbFileName, data):
    authInformation = database.authenticate(dbFileName, [data])
    success = all([info["authSuccess"] for info in authInformation])
    if success:
        receiverClient = connections.getClient(data["to"])
        request = {
            'message' : 'new message'
            , 'from' : data["id"]
            , 'to' : data["to"]
            , 'message' : data["message"]  
        }   

        if receiverClient is not None:
            await receiverClient.send(json.dumps({
                'requestToken': generateRequestToken()
                , **request
            }));

    

async def createChannel(websocket, dbFileName, data):
    password = data["password"]
    id = database.createChannel(dbFileName, password)
    if id == None:
        await requests.respond(websocket, data["requestId"], {
            'status': 'failed', 
        });
    else:
        await requests.respond(websocket, data["requestId"], {
            'status': 'success', 
            'id': id.hex(),
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
        """await websocket.send(json.dumps({
            'message' : 'new messages'
            , 'messages' : [{
                'requestToken' = generateRequestToken()
                , **message
            } for message in database.getMessages(data["channels"])]
        }))"""

async def counter(websocket, path, dbFileName):
    # register(websocket) sends user_event() to websocket
    #await register(websocket)
    openRequestTokens = set()   
    authenticatedChannelIds = set()
    try:
        async for message in websocket:
            data = json.loads(message)
            logging.debug("%s, %s", data, path)

            requestId = data["requestId"];
            if requestId in openRequestTokens:
                # request token collision or request has already been added to the list
                # please try again with a different request token or don't bother, we already got the message
                await requests.send(websocket, requestId, { 
                    'status': 'failed', 
                    'reason': 'request id collision'
                });
                continue
            else:
                openRequestTokens.add(requestId)
                
            if data["message"] == "create channel":
                await createChannel(websocket, dbFileName, data)
            elif data["message"] == "authenticate":
                await authenticate(websocket, dbFileName, data)
            elif data["message"] == "send message":
                await sendMessage(websocket, dbFileName, data)

            openRequestTokens.remove(requestId)
    finally:
        connections.forget(websocket)

def init(server, port, dbFileName):
    start_server = websockets.serve(functools.partial(counter,dbFileName=dbFileName), server, port)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

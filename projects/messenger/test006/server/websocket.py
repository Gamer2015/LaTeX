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
import messages

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

    

async def createChannel(websocket, dbFileName, message):
    password = message["password"]
    id = database.createChannel(dbFileName, password)
    if id == None:
        await messages.respond(websocket, message, {
            'status': 'failed', 
        });
    else:
        await messages.respond(websocket, message, {
            'status': 'success', 
            'id': id.hex(),
        });

async def authenticate(websocket, dbFileName, message):
    channels = message["channels"];
    for channel in channels:
        channel["id"] = bytes.fromhex(channel["id"])

    authInformation = database.authenticate(dbFileName, channels)
    success = all([info["authSuccess"] for info in authInformation])
    #activeSession = connections.activeSession(channels)
    anyActive = connections.anyActive(channels)
    # more flexibility possible, but good enough for now
    if success == False or anyActive == True:
        await messages.respond(websocket, message, {
            'status': 'failed'
        }); 
    else:
        connections.remember(websocket, message["channels"])
        await messages.respond(websocket, message, {
            'status': 'success'
        });
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
            message = json.loads(message)
            if message["acknowledge"] == True:
                await messages.acknowledge(websocket, message);
                
            if message["subject"] == "create channel":
                await createChannel(websocket, dbFileName, message)
            elif message["subject"] == "authenticate":
                await authenticate(websocket, dbFileName, message)
            elif message["subject"] == "send message":
                await sendMessage(websocket, dbFileName, message)
    finally:
        connections.forget(websocket)

def init(server, port, dbFileName):
    start_server = websockets.serve(functools.partial(counter,dbFileName=dbFileName), server, port)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

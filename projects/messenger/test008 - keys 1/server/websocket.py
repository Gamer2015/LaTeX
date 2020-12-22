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


async def sendMessage(client, dbFileName, message):
    if( connections.verify(client, message["from"]) 
        and database.verify(client, {
            "id": message["from"], "password": message["password"]
        })):
        receiverClient = connections.getClient(message["to"])

        if receiverClient is not None:
            await messages.send(receiverClient, 'new message', {
                'from' : message["from"]
                , 'to' : message["to"]
                , 'message' : message["message"]  
            }, True)


async def createEntities(client, dbFileName, message):
    ids = database.createEntities(dbFileName, message["entities"])
    if ids == None:
        await messages.respond(client, message, {
            'status': 'failed', 
        });
    else:
        await messages.respond(client, message, {
            'status': 'success', 
            'ids': [ids.hex() for id in ids]
        });

async def authenticate(client, dbFileName, message):
    entities = message["entities"]
    success = database.verify(dbFileName, entities)
    #activeSession = connections.activeSession(entities)
    anyActive = connections.anyActive(entities)
    # more flexibility possible, but good enough for now
    if success == False or anyActive == True:
        await messages.respond(client, message, {
            'status': 'failed'
        }); 
    else:
        connections.remember(client, entities)
        await messages.respond(client, message, {
            'status': 'success'
        });

async def connector(client, path, dbFileName):
    # register(client) sends user_event() to client
    #await register(client)
    openRequestTokens = set()   
    authenticatedChannelIds = set()
    try:
        async for message in client:
            message = json.loads(message)
            if message["header"]["acknowledge"] == True:
                await messages.acknowledge(client, message);
            
            subject = message["header"]["subject"]
            if subject == "create entities":
                await createEntities(client, dbFileName, message)
            elif subject == "authenticate":
                await authenticate(client, dbFileName, message)
            elif subject == "send message":
                await sendMessage(client, dbFileName, message)
    finally:
        connections.forget(client)

def init(server, port, dbFileName):
    start_server = websockets.serve(functools.partial(connector,dbFileName=dbFileName), server, port)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

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

"""
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
            """

async def get(client, dbFileName, message):
    accounts = message["accounts"]
    print(accounts)
    packages = database.get(dbFileName, accounts)
    await messages.respond(client, message, {
        'status': 'success',
        'packages': packages
    })

async def save(client, dbFileName, message):
    accounts = message["accounts"]
    packages = message["packages"]
    timestamp = message["timestamp"]
    
    changes = database.save(dbFileName, accounts, packages, timestamp) 
    print(changes)
    if changes != False and len(changes) != 0:
        client2changedAccountIds = {}
        for accountId in changes:
            otherClients = connections.getClients(accountId)

            for otherClient in otherClients:
                if otherClient != client:
                    try: 
                        accountIds = client2changedAccountIds[otherClient]
                    except:
                        accountIds = set()
                    accountIds.add(accountId)
                    client2changedAccountIds[otherClient] = accountIds

        for client, accountIds in client2changedAccountIds.items():
            accountIds = list(accountIds)
            await messages.send(otherClient, 'packages changed', {
                'accountIds': accountIds
            })

async def authenticate(client, dbFileName, message):
    accounts = message["accounts"]
    success = database.verify(dbFileName, accounts)
    # activeSession = connections.activeSession(entities)
    # anyActive = connections.anyActive(entities)
    # more flexibility possible, but good enough for now
    if success == False:
        await messages.respond(client, message, {
            'status': 'failed'
        }); 
    else:
        connections.remember(client, accounts)
        await messages.respond(client, message, {
            'status': 'success'
        });

async def createAccounts(client, dbFileName, message):
    ids = database.createAccounts(dbFileName, message["accounts"])
    if ids == None:
        await messages.respond(client, message, {
            'status': 'failed', 
        });
    else:
        await messages.respond(client, message, {
            'status': 'success', 
            'ids': [id.hex() for id in ids]
        });

async def connector(client, path, dbFileName):
    # register(client) sends user_event() to client
    #await register(client)
    openRequestTokens = set()   
    authenticatedChannelIds = set()
    try:
        async for message in client:
            message = json.loads(message)
            # if message["header"]["acknowledge"] == True:
            #     await messages.acknowledge(client, message);
            
            subject = message["header"]["subject"]
            if subject == "create accounts":
                await createAccounts(client, dbFileName, message)
            elif subject == "authenticate":
                await authenticate(client, dbFileName, message)
            elif subject == "save":
                await save(client, dbFileName, message)
            elif subject == "get":
                await get(client, dbFileName, message)
    finally:
        connections.forget(client)

def init(server, port, dbFileName):
    start_server = websockets.serve(functools.partial(connector,dbFileName=dbFileName), server, port)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

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
import utilities

# communication
import secrets


async def get(client, dbFileName, message):
    accounts = utilities.unpackAccounts(message["accounts"])

    packages, failedAccounts = database.get(dbFileName, accounts)
    await messages.respond(client, message, {
        'packages': utilities.packPackages(packages, set(["_id"])),
        "failed": utilities.packAccounts(failedAccounts)
    })

async def save(client, dbFileName, message):
    accounts = utilities.unpackAccounts(message["accounts"])
    packages = utilities.unpackPackages(message["packages"])
    
    successList, failedList = database.save(dbFileName, accounts, packages) 

    await messages.respond(client, message, {
        "successful" : utilities.packPackages(successList, set(["data"])),
        "failed" : utilities.packPackages(failedList, set(["data"]))
    })

    changedAccountIds = set([package["accountId"] for package in successList])
    clients2accountIds = connections.getClients(changedAccountIds)
    for otherClient, accountIds in clients2accountIds.items():
        accountIds = list(accountIds)
        await messages.send(otherClient, 'packages changed', {
            'accountIds': utilities.packBlobs(accountIds)
        })

async def authenticate(client, dbFileName, message):
    accounts = utilities.unpackAccounts(message["accounts"])
    successful, failed = database.verify(dbFileName, accounts)
    # activeSession = connections.activeSession(entities)
    # anyActive = connections.anyActive(entities)
    # more flexibility possible, but good enough for now
    connections.remember(client, [account["id"] for account in successful])
    await messages.respond(client, message, {
        "successful": utilities.packAccounts(successful),
        "failed": utilities.packAccounts(failed)
    });

async def createLogins(client, dbFileName, message):
    # loginId, password
    logins, failed1, failed0 = database.createLogins(dbFileName, message["accounts"])

    await messages.respond(client, message, {
        "logins": utilities.packLogins(logins),
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
            if subject == "create logins":
                await createLogins(client, dbFileName, message)
            elif subject == "authenticate":
                await authenticate(client, dbFileName, message)
            elif subject == "get":
                await get(client, dbFileName, message)
            elif subject == "save":
                await save(client, dbFileName, message)
            #elif subject == "delete":
            #    await delete(client, dbFileName, message)
    finally:
        connections.forget(client)

def init(server, port, dbFileName):
    start_server = websockets.serve(functools.partial(connector,dbFileName=dbFileName), server, port)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

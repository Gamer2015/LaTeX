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
    accounts = utilities.unpackAccounts(message["accounts"])

    packages, failedAccounts = database.get(dbFileName, accounts)
    await messages.respond(client, message, {
        'packages': utilities.packPackages(packages, set(["_id"])),
        "failed": utilities.packAccounts(failedAccounts)
    })

async def save(client, dbFileName, message):
    accounts = utilities.unpackAccounts(message["accounts"])
    packages = utilities.unpackPackages(message["packages"])
    
    print("packages before          ", message["packages"])
    print("packages after         ", packages)
    successList, failedList = database.save(dbFileName, accounts, packages) 

    print("successList           ", successList)
    await messages.respond(client, message, {
        "successful" : utilities.packPackages(successList, set(["data"])),
        "failed" : utilities.packPackages(failedList, set(["data"]))
    })

    changedAccountIds = set([package["accountId"] for package in successList])
    print("changedAccountIds1       ", changedAccountIds)
    print("activeClients       ", connections.activeClients())
    clients2accountIds = connections.getClients(changedAccountIds)
    print("changedAccountIds2.5     ", clients2accountIds)
    clients2accountIds.pop(client, None)
    print("changedAccountIds2       ", clients2accountIds)
    for otherClient, accountIds in clients2accountIds.items():
        accountIds = list(accountIds)
        print("accountIds           ", accountIds)
        await messages.send(otherClient, 'packages changed', {
            'accountIds': utilities.packBlobs(accountIds)
        })
"""
async def delete(client, dbFileName, message):
    accounts = message["accounts"]
    packages = message["packages"]
    
    accountIds = database.delete(dbFileName, accounts, packages) 

    if accountIds != False and len(accountIds) != 0:
        clients2accountIds = connections.getClients(accountIds)
        clients2accountIds.pop(client)
        for otherClient, accountIds in clients2accountIds.items():
            accountIds = list(accountIds)
            await messages.send(otherClient, 'packages changed', {
                'accountIds': accountIds
            })
"""
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

async def createAccounts(client, dbFileName, message):
    accounts = database.createAccounts(dbFileName, message["accounts"])

    await messages.respond(client, message, {
        "accounts": utilities.packAccounts(accounts),
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

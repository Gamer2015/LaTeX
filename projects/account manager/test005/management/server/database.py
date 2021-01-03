import logging
logging.basicConfig(level=logging.DEBUG)

import sqlite3
from sqlite3 import Error
import datetime 
import time

import secrets
import bcrypt

import functools
import utilities

idLength = 8

def adapt_datetime(dt_obj):
    return int(dt_obj.timestamp() * 1000)

sqlite3.register_adapter(datetime.datetime, adapt_datetime) 

def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate

def dbConnect(dbFileName):
    db = sqlite3.connect(dbFileName)
    db.row_factory = sqlite3.Row
    return db

"""
timestamp date
, accountId blob NOT NULL
, key text NOT NULL
, data blob
, PRIMARY KEY(accountId, key)
"""
# never share without verifying

STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"
def addStatusWrapper(entity, status=STATUS_SUCCESS, reason=None):
    tmp = {}
    keys = []
    for key in entity:
        tmp[key] = entity[key]
        keys.append(key)

    for key in keys:
        entity.pop(key, None)


    entity["status"] = status
    if reason != None:
        entity["reason"] = reason
    entity["entity"] = tmp

def insertEntity(db, cursor, table, entity, keyGenerator, keyPath):
    entity[keyPath] = keyGenerator()
    try:
        insert(cursor, table, entity)
        db.commit()    
        addStatusWrapper(entity) 
    except sqlite3.IntegrityError as err:
        # ignore unique constraints, just try again
        if("UNIQUE constraint failed: " not in err.args[0]):
            raise
    except Exception as exception:
        # something else went terribly wrong, abort ...
        entity.pop(keyPath, None)
        addStatusWrapper(entity, STATUS_FAILED, exception)

def insertEntities(db, cursor, table, entities, keyGenerator, keyPath):
    for entity in entities:
        insertEntity(db, cursor, table, entity, keyGenerator, keyPath)

def sendMessages(dbFileName, accounts, messages):
    db = dbConnect(dbFileName)
    c = db.cursor()

    successful, failed = verify(c, accounts, True)
    
    authenticatedAccountIds = set()
    for account in successful:
        authenticatedAccountIds.add(account["id"])

    senderIds = [message["senderId"] for message in messages]
    c.execute("""
        SELECT id
        FROM {identities}
        INNER JOIN {accounts} ON {accounts}.id = {identities}.accountId
        WHERE {identities}.id in ({senderIds}) 
        AND {accounts}.id in ({authenticatedAccountIds})
    """.format(
        identities="identities"
        , accounts="accounts"
        , senderIds=placeholders(senderIds)
        , authenticatedAccountIds=placeholders(authenticatedAccountIds)
    ), senderIds, authenticatedAccountIds)

    authenticatedIdentities = set()
    for row in c.fetchall():
        authenticatedIdentities.add(row["id"])


    recipientIds = set()
    for message in messages:
        for recipient in message["to"]:
            recipientIds.add(recipient)

    c.execute("""
        SELECT id
        FROM {identities}
        WHERE id in ({recipientIds}) 
    """.format(
        identities="identities"
        , recipientIds=placeholders(recipientIds)
    ), recipientIds)

    validRecipientIds = set()
    for row in c.fetchall():
        validRecipientIds.add(row["id"])


    timestamp = datetime.datetime.now()
    messageWrappers = []
    validMessages = []
    for message in messages:
        # send to all recipients
        # more information about who received it may be present in the message body
        for recipient in forceSet(message["recipientIds"]):
            tmp = {
                "senderId": message["senderId"]
                , "recipientId": recipient
                , "body": message["body"]
                , "timestamp": timestamp
                , "expires": message["expires"]
            }

            if message["senderId"] not in authenticatedIdentities:
                # authentication failed
                addStatusWrapper(tmp, STATUS_FAILED, "authentication failed")
            elif recipient not in validRecipientIds:
                # invalid recipient id
                addStatusWrapper(tmp, STATUS_FAILED, "invalid recipient")
            else:
                insertEntity(db, c, "messages", tmp, generateMessageId, 'id')

            messageWrappers.append(tmp)  

    return messageWrappers, failed;

def generateIdentityId():
    id = secrets.token_bytes(idLength) 
    return id
def createIdentities(dbFileName, accounts, amount):
    db = dbConnect(dbFileName)
    c = db.cursor()

    successAccounts, failedAccounts = verify(c, accounts, True)

    identityCounter = {}
    for account in successAccounts:
        identityCounter[account["id"]] = 0

    total = amount * len(successAccounts)
    identities = []
    while len(identities) < total:
        cycleIdentities = []
        for account in successAccounts:
            for i in range(amount-identityCounter[account["id"]]):
                cycleIdentities.append({
                    "accountId": account["id"],
                    "username": account["username"]
                })

        insertEntities(db, c, 'identities', cycleIdentities, generateIdentityId, 'id')
        createdIdentities = ([
            identity["entity"] for identity in cycleIdentities if identity["status"] == "success"
        ])
        for identity in createdIdentities:
            identityCounter[identity["accountId"]] = identityCounter[identity["accountId"]] + 1

        identities.extend(createdIdentities)

    return identities, failedAccounts

def getPackages(dbFileName, accounts):
    db = dbConnect(dbFileName)
    c = db.cursor()

    # need to authenticate before retrieving
    successAccounts, failedAccounts = verify(c, accounts, True)

    packages = []
    for account in successAccounts:
        c.execute("""
            SELECT {packages}.id, data, key
            , username
            FROM {packages}
            INNER JOIN {accounts} ON {accounts}.id = {packages}.accountId
            WHERE username = ? 
            AND timestamp >= ? 
        """.format(
            packages="packages",
            accounts='accounts'
        ), (account['username'], account["timestamp"] if "timestamp" in account else 0))

        packages.extend([{
            "username": row["username"],
            "id": row["id"],
            "key": row["key"],
            "data": row["data"],
        } for row in c.fetchall()])


    return packages, failedAccounts


def generatePackageId():
    id = secrets.token_bytes(idLength) 
    return id
def savePackages(dbFileName, accounts, packages):
    db = dbConnect(dbFileName)
    c = db.cursor()

    if len(packages) == 0:
        # nothing to do
        return packages

    # add timestamp and isolate from the outside
    timestamp = datetime.datetime.now()
    packages = [{
        "timestamp": timestamp
        , **package
    } for package in packages]

    # need to authenticate before saving
    accSuccess, accFailed = verify(c, accounts, True)
    
    username2verifiedId = {}
    for account in accSuccess:
        username2verifiedId[account["username"]] = account["id"]
    
    authenticated = []
    for package in packages:
        if package["username"] in username2verifiedId:
            # add authentication
            package["accountId"] = username2verifiedId[package["username"]]
            authenticated.append(package)
        else:
            addStatusWrapper(package, STATUS_FAILED, "authentication failed")


    insertList = []
    updateList = []

    authenticatedUpdates = []
    for package in authenticated:
        if "id" in package:
            authenticatedUpdates.append(package)
        else:
            insertList.append(package)

    for account in accSuccess:
        accountId = account["id"]
        accPackages = [
            package for package in authenticatedUpdates if package["accountId"] == accountId
        ]
        packageIds = [package["id"] for package in accPackages]
        c.execute("""
            SELECT accountId, id, timestamp
            FROM packages 
            WHERE accountId=? 
            AND id in ({packageIds})
        """.format(
            packageIds=placeholders(packageIds)
        ), tuple([account["id"], *packageIds]))

        old = {}
        for row in c.fetchall():
            old[row["id"]] = row

        for package in accPackages:
            if package["id"] not in old:
                # create a new record if none exist with that id
                insertList.append(package)
            else:
                updateList.append(package)

    insertEntities(db, c, 'packages', insertList, generatePackageId, 'id')

    try:
        update(c, 'packages', updateList)
        db.commit()
        for package in updateList:
            addStatusWrapper(package)
    except:
        for package in updateList:
            addStatusWrapper(package, STATUS_FAILED, "update failed")

    # remove authentication, revert to username
    for package in authenticated:
        package.pop("accountId", None)

    return packages



def verify(cursor, accounts, keepAuthentication=False):
    accounts = utilities.forceIterable(accounts)

    usernames = [account["username"] for account in accounts]
    cursor.execute("""
        SELECT id, username, password 
        FROM accounts
        WHERE username in ({usernames})
    """.format(
        usernames=placeholders(usernames)
    ), usernames)

    rows = {};
    for row in cursor.fetchall():
        rows[row["username"]] = row

    successList = []
    failedList = []
    for account in accounts:
        success = True 
        password = '' # 60 should be the length of the hashed password
        if account["username"] in rows: 
            row = rows[account["username"]]
            password = row["password"]
        else:
            success = False
        success = success and bcrypt.checkpw(account["password"], password)

        if success:
            account["id"] = row["id"]
            successList.append(account)
        else:
            failedList.append(account)

    if keepAuthentication == False:
        for account in successList:
            account.pop("id", None)

    return successList, failedList


def generateAccountId():
    id = secrets.token_bytes(idLength) 
    return id
def createAccounts(dbFileName, accounts):
    db = dbConnect(dbFileName)
    c = db.cursor()

    usernames = [account["username"] for account in accounts]
    c.execute("""
        SELECT username 
        FROM accounts
        WHERE username in ({usernames})
    """.format(
        usernames=placeholders(usernames)
    ), usernames)
    invalidUsernames = set([account["username"] for account in c.fetchall()])

    insertList = []
    for account in accounts:
        if account["username"] not in invalidUsernames:
            salt = bcrypt.gensalt()
            account['password'] = bcrypt.hashpw(account['password'], salt)
            insertList.append(account)
        else:
            addStatusWrapper(account, STATUS_FAILED, "username is already taken")
    
    insertEntities(db, c, 'accounts', insertList, generateAccountId, 'id')

    return accounts
"""
def generateDeviceId():
    id = secrets.token_bytes(idLength) 
    while id[0] == 0:
        id =  secrets.token_bytes(idLength)
    return id
def createDevices(dbFileName, devices):
    return createAuthenticationEntities(dbFileName, 'devices', devices, generateDeviceId)
"""
"""
    if isinstance(passwords, list) == False:
        passwords = [passwords]
    elif len(passwords) == 0:
        return []

    db = dbConnect(dbFileName)
    c = db.cursor()

    accounts = [{
        "password": password
    } for password in passwords]

    for account in accounts:
        salt = bcrypt.gensalt()
        account['password'] = bcrypt.hashpw(account['password'], salt)

    # create accounts
    for account in accounts:
        for i in range(1000000):
            account['id'] = generateId()
            try:
                insert(c, 'accounts', account)
                db.commit()     
                account['inserted'] = True
                break
            except:
                pass

    if all([account["inserted"] for account in accounts]):
        return [account["id"] for account in accounts];
    else:
        ids = [account["id"] for account in accounts if account["inserted"]]
        c.execute(""
            + "DELETE FROM accounts "
            + "WHERE id in (" + placeholders(ids) + ")", ids
        )
        db.commit()
        return None

def createDevices(dbFileName, passwords):
    if isinstance(passwords, list) == False:
        passwords = [passwords]
    elif len(passwords) == 0:
        return []

    db = dbConnect(dbFileName)
    c = db.cursor()

    devices = [{
        "password": password
    } for password in passwords]

    for device in devices:
        salt = bcrypt.gensalt()
        device['password'] = bcrypt.hashpw(device['password'], salt)

    # create devices
    for device in devices:
        for i in range(1000000):
            device['id'] = generateId()
            try:
                insert(c, 'devices', device)
                db.commit()     
                device['inserted'] = True
                break
            except:
                pass

    if all([device["inserted"] for device in devices]):
        return [device["id"] for device in devices];
    else:
        ids = [device["id"] for device in devices if device["inserted"]]
        c.execute(""
            + "DELETE FROM devices "
            + "WHERE id in (" + placeholders(ids) + ")", ids
        )
        db.commit()
        return None
"""

"""
def createUsers(dbFileName, users):
    db = dbConnect(dbFileName)
    c = db.cursor()
    
    salt = bcrypt.gensalt()
    user = {
        "password": bcrypt.hashpw(user['password'], salt) 
    }

    # create user
    inserted = False
    for i in range(1000000): # try a few ids if before aborting
        user['id'] = generateId()
        try:
            c.execute(""
                + "INSERT INTO users(id, password) "
                + "VALUES(?,?) ", (
                user['id'], user['password'],
            ))
            db.commit()  
            inserted = True 
            break
        except:
            pass

    if inserted == True:
        return user["id"]
    else:
        return None"""

def fieldNameList(cursor, table):
    cursor.execute('select * from ' + table)
    return [description[0] for description in cursor.description]

def pkFieldNameList(cursor, table):
    cursor.execute("PRAGMA table_info(" + table + ")")
    columns = cursor.fetchall()
    pkFields = [None]*len(columns);
    for column in columns: # ['cid', 'name', 'type', 'notnull', 'dflt_value', 'pk']
        pkIndex = column['pk']-1
        if pkIndex != -1:
            pkFields[pkIndex] = column['name']
    return [field for field in pkFields if field is not None]

def fieldQuery(fields):
    return ','.join(fields)
def placeholders(fields):
    return ','.join(['?']*len(fields))
def assignments(fields):
    return ','.join([field + "=?" for field in fields])
def queries(fields):
    return ' AND '.join([field + "=?" for field in fields])
def tuples(objects, fields):
    if isinstance(objects, list) == False:
        return tuple([
            obj[field] if field in obj else None for field in fields
        ])
    else:
        return [tuple([
            obj[field] if field in obj else None for field in fields
        ]) for obj in objects]

def insert(cursor, table, objects):
    objects = utilities.forceList(objects)
    if len(objects) == 0:
        return

    # find columns of the table, only data in columns can be set
    fields = fieldNameList(cursor, table)

    cursor.executemany("""
        INSERT INTO {table} VALUES ({fieldValues})
    """.format(
        table=table, 
        fieldValues=placeholders(fields)
    ), tuples(objects, fields))

def update(cursor, table, objects):
    objects = utilities.forceList(objects)
    if len(objects) == 0:
        return

    # find columns of the table, only data in columns can be updated
    fields = fieldNameList(cursor, table)

    # upgrade rows where the primary keys hold
    pkFields = pkFieldNameList(cursor, table)

    # gather objects that have the same fields set
    # used so we can use executemany
    queryCategories = {}
    for obj in objects:
        objectFields = []
        for field in fields:
            if field in obj:
                objectFields.append(field)

        category = ' '.join(objectFields)
        try:
            existing = queryCategories[category]
        except:
            existing = []
        existing.append(obj)
        queryCategories[category] = existing

    for category, objects in queryCategories.items():
        fields = category.split(" ")

        cursor.executemany("""
            UPDATE {table}
            SET {fieldAssignments}
            WHERE {pkFieldQueries}
        """.format(
            table=table,
            fieldAssignments=assignments(fields),
            pkFieldQueries=queries(pkFields)
        ), tuples(objects, [*fields, *pkFields]))

def dbConnect(dbFileName):
    db = sqlite3.connect(dbFileName)
    db.row_factory = sqlite3.Row
    return db


@static_vars(counter=0)
def initializeDatabase(dbFileName, differenceHistory):
    db = dbConnect(dbFileName)
    cursor = db.cursor()

    try: # initialize versioning system
        cursor.execute('CREATE TABLE versions (version integer)')
        insert(cursor, 'versions', {'version': 0})
        # save changes
        db.commit() 
    except sqlite3.OperationalError as e:
        # initializing may fail if it has already been initialized
        pass


    cursor.execute('SELECT version FROM versions ORDER BY version DESC LIMIT 1')
    lastVersion = cursor.fetchone()['version'];
    
    newVersion = False
    for difference in differenceHistory:
        initializeDatabase.counter += 1
        if lastVersion < initializeDatabase.counter:
            difference(db, cursor);
            lastVersion += 1
            newVersion = True

    if newVersion == True:
        insert(cursor, 'versions', {'version': lastVersion})  
        db.commit()

def createAccountDatabase(database, cursor):
    cursor.execute("""
        CREATE TABLE accounts (
        id blob PRIMARY KEY
        , username text NOT NULL UNIQUE
        , password text NOT NULL
    )""")
    cursor.execute('CREATE INDEX username ON accounts(username)')
    database.commit()  

def createPackageDatabase(database, cursor):
    cursor.execute("""
        CREATE TABLE packages (
        id blob NOT NULL
        , accountId blob NOT NULL
        , timestamp integer
        , data blob
        , key string NOT NULL
        , PRIMARY KEY(accountId, id)
    )""")
    cursor.execute('CREATE INDEX timestamp ON packages(timestamp)')
    database.commit()

def createIdentityDatabase(database, cursor):
    cursor.execute("""
        CREATE TABLE identities (
        id blob PRIMARY KEY
        , accountId blob NOT NULL
    )""")
    cursor.execute('CREATE INDEX accountId ON identities(accountId)')
    database.commit()

def createMessageDatabase(database, cursor):
    cursor.execute("""
        CREATE TABLE messages (
        id blob PRIMARY KEY
        , senderId blob NOT NULL
        , recipientId blob NOT NULL
        , body text
        , timestamp integer
        , expires integer
    )""")
    cursor.execute('CREATE INDEX recipientId ON messages(recipientId)')
    database.commit()

def init(dbFileName):
    initializeDatabase(dbFileName, [
        createAccountDatabase,
        createPackageDatabase,
        createIdentityDatabase,
        createMessageDatabase,
        #createActiveLoginDatabase,
        #createDevicesDatabase,
        #createDeviceAccountsDatabase
    ])

"""
db = dbConnect(dbFileName)
db.row_factory = sqlite3.Row

c = db.cursor()
# upgrade tables if a new version is available
# upgrading from one version to another must not fail
# throw if an upgrade does not work
c.execute('SELECT version FROM ' + versionsTableName + ' ORDER BY version DESC LIMIT 1')
lastVersion = c.fetchone();
if lastVersion['version'] < 1:
    # setup tables
    c.execute('CREATE TABLE ' + passwordsTableName + ' (id blob PRIMARY KEY, passwordHash text NOT NULL)')    

    # update version
    n = datetime.datetime.now() 
    c.execute('INSERT INTO ' + versionsTableName + ' VALUES (1, ?)', (n,))   
    # save changes
    db.commit()
elif lastVersion['version'] < 2:
    pass # version 2 has not yet been defined"""




"""
dbFileName = "./tmp1.db"
initDb(dbFileName) 
db = sqlite3.connect(dbFileName)
c = db.cursor()     

id = secrets.token_bytes(8)
password = secrets.token_bytes(255)
#c.execute("INSERT INTO stocks VALUES (?,?)", (id,password))

id = secrets.token_bytes(8)
password = secrets.token_bytes(255)
#c.execute("INSERT INTO stocks VALUES (?,?)", (id,password))

db.commit()

c.execute("SELECT id FROM stocks")
rows = c.fetchall() 
print(rows)


db.close()
"""
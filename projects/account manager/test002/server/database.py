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


def makeStatusEntity(entity, status="success", reason=None):
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

def insertEntities(db, cursor, table, entities, keyGenerator, keyPath, attempts=1000):
    for entity in entities:
        for i in range(attempts):
            entity[keyPath] = keyGenerator()
            try:
                insert(cursor, table, entity)
                db.commit()    
                makeStatusEntity(entity) 
                break
            except:
                if i==attempts-1:
                    makeStatusEntity(entity, "failed")

def get(dbFileName, accounts):
    # need to authenticate before retrieving
    successAccounts, failedAccounts = verify(dbFileName, accounts, True)

    db = dbConnect(dbFileName)
    c = db.cursor()

    packages = []
    for account in successAccounts:
        ("""
            SELECT {storage}.accountId, {storage}.packageId, {storage}.data
            , {accounts}.id, {accounts}.username
            FROM {storage}
            INNER JOIN {accounts} ON {accounts}.id = {storage}.accountId
            WHERE {accounts}.username = ? 
            AND {storage}.timestamp >= ? 
        """.format(
            storage="accountStorage",
            accounts='accounts'
        ), (account['username'], account["timestamp"] if "timestamp" in account else 0))

        packages.extend([{
            username: row["username"],
            packageId: row["packageId"],
            data: row["data"]
        } for row in c.fetchall()])

    return packages, failedAccounts;


def generatePackageId():
    id = secrets.token_bytes(idLength) 
    while id[0] == 0:
        id =  secrets.token_bytes(idLength)
    return id

def save(dbFileName, accounts, packages):
    if len(packages) == 0:
        # nothing to do
        return packages

    timestamp = datetime.datetime.now()
    for package in packages:
        package["timestamp"] = timestamp

    # need to authenticate before saving
    accSuccess, accFailed = verify(dbFileName, accounts, True)
    
    username2verifiedId = {}
    for account in accSuccess:
        username2verifiedId[account["username"]] = account["id"]
    
    authenticated = []
    for package in packages:
        if package["accountId"] in username2verifiedId:
            # add authentication
            package["accountId"] = username2verifiedId[package["username"]]
            authenticated.append(package)
        else:
            makeStatusEntity(package, "failed", "account authentication failed")


    db = dbConnect(dbFileName)
    c = db.cursor()

    insertList = []
    updateList = []

    for account in accSuccess:
        accountId = account["id"]
        accPackages = [
            package for package in authenticated if package["accountId"] == accountId
        ]
        packageIds = [package["packageId"] for package in accPackages]
        c.execute("""
            SELECT accountId, packageId, timestamp
            FROM accountStorage 
            WHERE accountId=? 
            AND packageId in ({packageIds})
        """.format(
            packageIds=placeholders(packageIds)
        ), tuple([account["id"], *packageIds]))

        old = {}
        for row in c.fetchall():
            old[row["packageId"]] = row

        for package in accPackages:
            if package["packageId"] not in old:
                # create a new record if none exist with that id
                insertList.append(package)
            else:
                updateList.append(package)

    insertEntities(db, c, 'accountStorage', insertList, generatePackageId, 'packageId')

    try:
        update(c, 'accountStorage', updateList)
        db.commit()
        for package in updateList:
            makeStatusEntity(package)
    except:
        for package in updateList:
            makeStatusEntity(package, "failed", "update failed")

    # remove authentication, revert to username
    for package in authenticated:
        package.pop("accountId", None)

    return packages



def verify(dbFileName, accounts, keepAuthentication=False):
    accounts = utilities.forceIterable(accounts)

    db = dbConnect(dbFileName)
    c = db.cursor()

    usernames = [account["username"] for account in accounts]
    c.execute("""
        SELECT id, username, password 
        FROM accounts
        WHERE username in ({usernames})
    """.format(
        usernames=placeholders(usernames)
    ), usernames)

    rows = {};
    for row in c.fetchall():
        rows[row["username"]] = row

    successList = []
    failedList = []
    for account in accounts:
        success = True 
        password = '' # 60 should be the length of the hashed password
        if account["username"] in rows: 
            row = rows[account["username"]]
            account["id"] = row["id"]
            password = row["password"]
        else:
            success = False
        success = success and bcrypt.checkpw(account["password"], password)

        if success:
            successList.append(account)
        else:
            failedList.append(account)

    if keepAuthentication == False:
        for account in accounts:
            account.pop("id", None)

    return successList, failedList


def generateAccountId():
    id = secrets.token_bytes(idLength) 
    while id[0] == 0:
        id =  secrets.token_bytes(idLength)
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
            makeStatusEntity(account, "failed", "username is already taken")
    
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
        , password NOT NULL
    )""")
    cursor.execute('CREATE INDEX username ON accounts(username)')
    database.commit()  

def createAccountStorage(database, cursor):
    cursor.execute("""
        CREATE TABLE accountStorage (
        accountId blob NOT NULL
        , packageId blob NOT NULL
        , timestamp integer
        , data blob
        , PRIMARY KEY(accountId, packageId)
    )""")
    cursor.execute('CREATE INDEX timestamp ON accountStorage(timestamp)')
    database.commit()

def init(dbFileName):
    initializeDatabase(dbFileName, [
        createAccountDatabase,
        createAccountStorage,
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
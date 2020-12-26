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
def get(dbFileName, accounts):
    successList, failedList = verify(dbFileName, accounts)

    db = dbConnect(dbFileName)
    c = db.cursor()

    packages = []
    for account in successList:
        table = "accountStorage"
        fields = fieldNameList(c, table)
        c.execute("""
            SELECT {fieldQuery}
            FROM {table}
            WHERE accountId = ? 
            AND timestamp > ?
        """.format(
            fieldQuery=fieldQuery(fields),
            table=table
        ), (account['id'], account["timestamp"]))

        for row in c.fetchall():
            record = {}
            for field in fields:
                record[field] = row[field]
            packages.append(record)

    return packages, failedList;


def generatePackageId():
    id = secrets.token_bytes(idLength) 
    while id[0] == 0:
        id =  secrets.token_bytes(idLength)
    return id

def save(dbFileName, accounts, packages):
    successList = []
    failedList = []
    if len(packages) == 0:
        return successList, failedList

    timestamp = datetime.datetime.now()
    for package in packages:
        package["timestamp"] = timestamp

    # never save without verifying
    accSuccess, accFailed = verify(dbFileName, accounts)
    verifiedAccountIds = set([account["id"] for account in accSuccess])
    unverifiedAccountIds = set([account["id"] for account in accFailed])

    tmpPackages = []
    for package in packages:
        if package["accountId"] in verifiedAccountIds:
            tmpPackages.append(package)
        else:
            failedList.append(package)
    packages = tmpPackages


    db = dbConnect(dbFileName)
    c = db.cursor()

    insertList = []
    updateList = []

    tmpPackages = []
    for package in packages:
        if package["_id"] != None:
            # all of those want to get a new id
            insertList.append(package)
        else:
            tmpPackages.append(package)
    packages = tmpPackages

    for account in accSuccess:
        accountId = account["id"]
        accPackages = [package for package in packages if package["accountId"] == accountId]
        ids = [package["id"] for package in accPackages]
        c.execute("""
            SELECT accountId, id, timestamp
            FROM accountStorage 
            WHERE accountId=? 
            AND id in ({ids})
        """.format(
            ids=placeholders(ids)
        ), tuple([accountId, *ids]))

        old = {}
        for row in c.fetchall():
            old[row["id"]] = row

        for package in accPackages:
            if package["id"] not in old:
                # create a new record if none exist with that id
                # store id in _id so that the client will know which package this is
                package["_id"] = package["id"]
                insertList.append(package)
            else:
                updateList.append(package)

    attempts = 1000000
    for package in insertList:
        for i in range(attempts):
            package["id"] = generatePackageId()
            try:
                insert(c, 'accountStorage', package)
                db.commit()
                successList.append(package)
                break
            except:
                if i == attempts-1:
                    failedList.append(package)

    try:
        update(c, 'accountStorage', updateList)
        db.commit()
        successList.extend(updateList)
    except:
        failedList.extend(updateList)
        pass

    return successList, failedList



def verify(dbFileName, accounts):
    accounts = utilities.forceIterable(accounts)

    db = dbConnect(dbFileName)
    c = db.cursor()

    ids = [account["id"] for account in accounts]
    c.execute("""
        SELECT id, password 
        FROM accounts
        WHERE id in ({ids})
    """.format(
        ids=placeholders(ids)
    ), ids)

    rows = {};
    for row in c.fetchall():
        rows[row["id"]] = row["password"]

    successList = []
    failedList = []
    for account in accounts:
        success = True 
        password = '' # 60 should be the length of the hashed password
        if account["id"] in rows: 
            password = rows[account["id"]]
        else:
            success = False
        success = success and bcrypt.checkpw(account["password"], password)
        if success:
            successList.append(account)
        else:
            failedList.append(account)
    return successList, failedList


def createAuthenticationEntities(dbFileName, table, passwords, entityIdGenerator):
    passwords = utilities.forceIterable(passwords)

    db = dbConnect(dbFileName)
    c = db.cursor()

    entities = [{
        "password": password
    } for password in passwords]

    for entity in entities:
        salt = bcrypt.gensalt()
        entity['password'] = bcrypt.hashpw(entity['password'], salt)

    # create entities
    successList = []
    failedList = []
    attempts = 1000000
    for entity in entities:
        for i in range(attempts):
            entity['id'] = entityIdGenerator()
            try:
                insert(c, table, entity)
                db.commit()     
                successList.append(entity)
                break
            except:
                if i == attempts-1:
                    failedList.append(entity)

    return successList, failedList

def generateAccountId():
    id = secrets.token_bytes(idLength) 
    while id[0] == 0:
        id =  secrets.token_bytes(idLength)
    return id
def createAccounts(dbFileName, passwords):
    return createAuthenticationEntities(dbFileName, 'accounts', passwords, generateAccountId)

def generateDeviceId():
    id = secrets.token_bytes(idLength) 
    while id[0] == 0:
        id =  secrets.token_bytes(idLength)
    return id
def createDevices(dbFileName, passwords):
    return createAuthenticationEntities(dbFileName, 'devices', passwords, generateDeviceId)

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

def createAccountsDatabase(database, cursor):
    cursor.execute("""
        CREATE TABLE accounts (
        id blob PRIMARY KEY
        , password NOT NULL
    )""")
    database.commit()  

def createDevicesDatabase(database, cursor):
    cursor.execute("""
        CREATE TABLE accounts (
        id blob PRIMARY KEY
        , password NOT NULL
    )""")    
    database.commit()  

def createAccountDevicesDatabase(database, cursor):
    cursor.execute("""
        CREATE TABLE accounts (
        accountId blob NOT NULL
        , deviceId blob NOT NULL
        , PRIMARY KEY(accountId, deviceId)
    )""")    
    database.commit()  

def createAccountStorage(database, cursor):
    cursor.execute("""
        CREATE TABLE accountStorage (
        accountId blob NOT NULL
        , id blob NOT NULL
        , timestamp integer
        , data blob
        , PRIMARY KEY(accountId, id)
    )""")
    cursor.execute('CREATE INDEX timestamp ON accountStorage(timestamp)')
    database.commit()

def init(dbFileName):
    initializeDatabase(dbFileName, [
        createAccountsDatabase,
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
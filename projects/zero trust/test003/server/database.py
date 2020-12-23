import logging
logging.basicConfig(level=logging.DEBUG)

import sqlite3
from sqlite3 import Error
import datetime 
import time

import secrets
import bcrypt

import functools

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
    if verify(dbFileName, accounts) == False:
        return None

    db = dbConnect(dbFileName)
    c = db.cursor()

    data = []
    for account in accounts:
        table = "accountStorage"
        fields = fieldNameList(c, table)
        c.execute("""
            SELECT """ + fieldQuery(fields) + """
            FROM """ + table + """ 
            WHERE accountId=? 
            AND timestamp > ?"""
        , (account['id'], account["timestamp"]))

        for row in c.fetchall():
            record = {}
            for field in fields:
                record[field] = row[field]
            data.append(record)

    return data;


# never save without verifying
def save(dbFileName, accounts, packages):
    if verify(dbFileName, accounts) == False:
        return False

    if isinstance(packages, list) == False:
        packages = [packages]
    elif len(packages) == 0:
        return False

    db = dbConnect(dbFileName)
    c = db.cursor()

    changes = set()
    insertList = []
    updateList = []
    for account in accounts:
        accPackages = [package for package in packages if package["accountId"] == account["id"]]
        keys = [package["key"] for package in accPackages]
        c.execute("""
            SELECT timestamp, key, data
            FROM accountStorage 
            WHERE accountId=? 
            AND key in ({keys})""".format(keys=placeholders(keys))
        , tuple([account['id'], *keys]))

        old = {}
        for row in c.fetchall():
            old[row["key"]] = row

        for package in accPackages:
            key = package["key"]
            data = package["data"]
            timestamp = datetime.datetime.now()
            record = {
                "accountId": account["id"],
                "key": key,
                "data": data,
                "timestamp": timestamp,
                "deleted" : package["deleted"],
                "crypto" : package["crypto"],
            }   
            if key not in old:
                insertList.append(record)
                changes.add(account["id"])
            else:
                if data != old[key]["data"]:
                    updateList.append(record)
                    changes.add(account["id"])

    insert(c, 'accountStorage', insertList)
    update(c, 'accountStorage', updateList)
    db.commit()

    return changes


def verify(dbFileName, accounts):
    if isinstance(accounts, list) == False:
        accounts = [accounts]
    elif len(accounts) == 0:
        return True

    db = dbConnect(dbFileName)
    c = db.cursor()

    # mapping
    accounts = [{
        'id': bytes.fromhex(account["id"])
        , 'password': account["password"]
    } for account in accounts]

    ids = [account["id"] for account in accounts]
    c.execute(""
        + "SELECT id, password " 
        + " FROM accounts "
        + " WHERE id in (" + placeholders(ids) + ")"
    , ids)

    rows = {};
    for row in c.fetchall():
        rows[row["id"]] = row["password"]

    success = True 
    for account in accounts:
        password = ' '*60 # 60 should be the length of the hashed password
        if account["id"] in rows: 
            password = rows[account["id"]]
        else:
            success = False
        success = success and bcrypt.checkpw(account["password"], password)
    return success

def generateId():
    id = secrets.token_bytes(idLength) 
    while id[0] == 0:
        id =  secrets.token_bytes(idLength)
    return id

def createAccounts(dbFileName, accounts):
    if isinstance(accounts, list) == False:
        accounts = [accounts]
    elif len(accounts) == 0:
        return []

    db = dbConnect(dbFileName)
    c = db.cursor()

    accounts = [{
        "password": account["password"]
    } for account in accounts]

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
    if isinstance(objects, list) == False:
        objects = [objects]
    elif len(objects) == 0:
        return

    fields = fieldNameList(cursor, table)

    query = "INSERT INTO " + table + " VALUES (" + placeholders(fields) + ") "
    values = tuples(objects, fields)
    cursor.executemany(query, values)

def update(cursor, table, objects):
    if isinstance(objects, list) == False:
        objects = [objects]
    elif len(objects) == 0:
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

        query = "UPDATE " + table + """
             SET """ + assignments(fields) + """
             WHERE """ + queries(pkFields)
        values = tuples(objects, [*fields, *pkFields])

        cursor.executemany(query, values)

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
    cursor.execute("""CREATE TABLE accounts (
        id blob PRIMARY KEY
        , password NOT NULL
    )""")    
    database.commit()  

def createAccountStorage(database, cursor):
    cursor.execute("""
        CREATE TABLE accountStorage (
        timestamp integer
        , accountId blob NOT NULL
        , key text NOT NULL
        , data blob
        , deleted text
        , crypto text
        , PRIMARY KEY(accountId, key)
    )""")
    cursor.execute('CREATE INDEX timestamp ON accountStorage(timestamp)')
    database.commit()

def init(dbFileName):
    initializeDatabase(dbFileName, [
        createAccountsDatabase,
        createAccountStorage
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
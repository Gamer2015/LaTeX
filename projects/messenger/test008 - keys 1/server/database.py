import logging
logging.basicConfig(level=logging.DEBUG)

import sqlite3
from sqlite3 import Error
import datetime 

import secrets
import bcrypt

import functools

idLength = 8

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

def verify(dbFileName, entities):
    db = dbConnect(dbFileName)
    c = db.cursor()

    # mapping
    entities = [{
        'id': bytes.fromhex(entity["id"])
        , 'password': entity["password"]
    } for entity in entities]

    ids = [entity["id"] for entity in entities]
    c.execute('SELECT id, password FROM entities WHERE id in ({seq})'.format(
        seq=','.join(['?']*len(ids))
    ), ids) 

    rows = {};
    for row in c.fetchall():
        rows[row["id"]] = row["password"]

    for entity in entities:
        success = True 
        password = ' '*60 # 60 should be the length of the hashed password
        if entity["id"] in rows: 
            password = rows[entity["id"]]
        else:
            success = False
        success = success and bcrypt.checkpw(entity["password"], password)
    return success

def verifyParents(dbFileName, entities):
    # verify parents
    parents = []
    parentIds = set()
    for entity in entities:
        if "parent" in entity:
            parent = entity["parent"]
            if parent == None:
                continue

            if parent["id"] not in parentIds:
                """ Don't do unnecessary checks.
                 If the parent data is known,
                 all the entities with the same parent
                should have the same data anyway """
                parentIds.add(parent["id"])
                parents.append(parent)

    return verify(dbFileName, parents)

"""
def authenticate(dbFileName, channels):
    db = dbConnect(dbFileName)
    c = db.cursor()

    for entity in channels:
        entity["id"] = bytes.fromhex(entity["id"])

    ids = [channel["id"] for channel in channels]
    c.execute('SELECT id, password FROM ' + passwordsTableName + ' WHERE id in ({seq})'.format(
        seq=','.join(['?']*len(ids))
    ), ids) 

    rows = {};
    foundRows = c.fetchall()
    for row in foundRows:
        rows[row["id"]] = row["password"]

    authInformation = []
    for channel in channels:
        success = True 
        password = channel["password"]
        passwordHash = ' '
        if channel["id"] in rows: 
            passwordHash =  rows[channel["id"]]
        else:
            success = False
        success = success and bcrypt.checkpw(password, passwordHash)
        authInformation.append({ 'id': channel["id"], 'authSuccess': success });
    return authInformation
"""
"""
def createChannel(dbFileName, password):
    db = dbConnect(dbFileName)
    c = db.cursor()

    id = generateId()
    salt = bcrypt.gensalt()
    passwordHash = bcrypt.hashpw(password, salt)

    inserted = False
    for i in range(1000000):
        try:
            c.execute('INSERT INTO ' + passwordsTableName + ' VALUES (?, ?)', (id,passwordHash))    
            db.commit()    
            inserted = True
            break
        except:
            id = generateId()
    if inserted:
        return id;
    else:
        return None
"""

def generateId():
    id = secrets.token_bytes(idLength) 
    while id[0] == 0:
        id =  secrets.token_bytes(idLength)
    return id

def createEntities(dbFileName, entities):
    db = dbConnect(dbFileName)
    c = db.cursor()

    if verifyParents(dbFileName, entities) == False:
        # quit if parent verification fails
        return None

    entities = [{
        "password": entity["password"],
        "id": entity["id"] if "id" in entity else None,
        "parent": entity["parent"]["id"] if "parent" in entity else None,
    } for entity in entities]

    for entity in entities:
        salt = bcrypt.gensalt()
        entity['password'] = bcrypt.hashpw(entity['password'], salt)

    # create entities
    for entity in entities:
        if "id" in entity:
            entity["inserted"] = True
            # entity has already been inserted for some reason
            continue

        for i in range(1000000):
            entity['id'] = generateId()
            try:
                insert(c, 'entities', entity)
                entity['inserted'] = True
                break
            except:
                pass

    db.commit()     

    if all([entity["inserted"] for entity in entities]):
        return [entity["id"] for entity in entities];
    else:
        return None

def insert(cursor, table, objects):
    if isinstance(objects, list) == false:
        objects = [objects]

    fieldCursor = cursor.execute('select * from ' + table)
    fields = [description[0] for description in cursor.description]

    cursor.execute('INSERT INTO ' + table + ' VALUES ({seq})'.format(
        seq=','.join(['?']*len(fields))
    ), [tuple(
        [obj[field] if field in obj else None for field in fields]
    ) for obj in objects])

@static_vars(counter=0)
def initializeDatabase(dbFileName, differenceHistory):
    db = dbConnect(dbFileName)
    cursor = db.cursor()

    try: # initialize versioning system
        cursor.execute('CREATE TABLE versions (version int)')
        insert(cursor, 'versions', {'version': 0})
        # save changes
        db.commit() 
    except Error as e:
        # initializing may fail if it has already been initialized
        pass

    cursor.execute('SELECT version FROM versions ORDER BY version DESC LIMIT 1')
    lastVersion = cursor.fetchone();

    newVersion = False
    for difference in differenceHistory:
        initializeDatabase.counter += 1
        if lastVersion['version'] < initializeDatabase.counter:
            difference(db, cursor);
            lastVersion += 1
            newVersion = True

    if newVersion == True:
        insert(cursor, 'versions', {'version': lastVersion})  

def createEntityDatabase(database, cursor):
    cursor.execute('CREATE TABLE entities (id blob PRIMARY KEY, parent blob, password text NOT NULL)')    
    database.commit()
    
def init(dbFileName):
    initializeDatabase(dbFileName, [
        createEntityDatabase
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
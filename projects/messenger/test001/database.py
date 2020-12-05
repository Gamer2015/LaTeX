import sqlite3
from sqlite3 import Error
import datetime 

import secrets
import bcrypt

idLength = 8
dbFileName = 'test.db'

def dbConnect(dbFileName):
    db = sqlite3.connect(dbFileName)
    db.row_factory = sqlite3.Row
    return db

def verifyChannel(dbFileName, id, password):
    db = dbConnect(dbFileName)
    c = db.cursor()

    c.execute('SELECT passwordHash FROM channels WHERE id=? LIMIT 1', (id,)) 
    row = c.fetchone()     
    if row == None:
        passwordHash = ''
    else:
        passwordHash = row["passwordHash"]
    return bcrypt.checkpw(password, passwordHash)

def createChannel(dbFileName, password):
    db = dbConnect(dbFileName)
    c = db.cursor()

    id = secrets.token_bytes(idLength)
    salt = bcrypt.gensalt()
    passwordHash = bcrypt.hashpw(password, salt)

    inserted = False
    for i in range(1000000):
        try:
            c.execute('INSERT INTO passwords VALUES (?, ?)', (id,passwordHash))    
            db.commit()    
            inserted = True
            break
        except:
            id = secrets.token_bytes(idLength)
    if inserted:
        return id;
    else:
        return None

def init(dbFileName):
    db = dbConnect(dbFileName)
    db.row_factory = sqlite3.Row

    c = db.cursor()

    try: # initialize database
        c.execute('CREATE TABLE versions (version int, date text)')
        n = datetime.datetime.now() 
        c.execute('INSERT INTO versions VALUES (0, ?)', (n,))   
        # save changes
        db.commit() 
    except Error as e:
        # initializing may fail if it has already been initialized
        pass

    # upgrade tables if a new version is available
    # upgrading from one version to another must not fail
    # throw if an upgrade does not work
    c.execute('SELECT version FROM versions ORDER BY version DESC LIMIT 1')
    lastVersion = c.fetchone();
    if lastVersion['version'] < 1:
        # setup tables
        c.execute('CREATE TABLE passwords (id blob PRIMARY KEY, passwordHash text NOT NULL)')    

        # update version
        n = datetime.datetime.now() 
        c.execute('INSERT INTO versions VALUES (1, ?)', (n,))   
        # save changes
        db.commit()
    elif lastVersion['version'] < 2:
        pass # version 2 has not yet been defined

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
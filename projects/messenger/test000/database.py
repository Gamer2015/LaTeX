import sys

if __name__ != '__main__':
    raise NotImplementedError("This file is not designed to be imported.")

import sqlite3
from sqlite3 import Error
import secrets

import datetime 



def createDbConnection(dbFileName):
    """ create a database connection to a SQLite database """
    try:
        return sqlite3.connect(dbFileName)
    except Error as e:
        print(e)


def initDb(dbFileName):
    db = createDbConnection(dbFileName)
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
        c.execute('CREATE TABLE passwords (id blob PRIMARY KEY, password blob NOT NULL)')    

        # update version
        n = datetime.datetime.now() 
        c.execute('INSERT INTO versions VALUES (1, ?)', (n,))   
        # save changes
        db.commit()
    elif lastVersion['version'] < 2:
        pass # version 2 has not yet been defined


dbFileName = "./tmp1.db"
initDb(dbFileName) 
db = createDbConnection(dbFileName)
c = db.cursor()     

id = bytes.fromhex('00000000000001')  
password = b''
c.execute("INSERT INTO passwords VALUES (?,?)", (id,password))

id = bytes.fromhex('00000000000000000001')  
password = b''
c.execute("INSERT INTO passwords VALUES (?,?)", (id,password))

db.commit()

c.execute("SELECT id FROM passwords")
rows = c.fetchall() 
print(rows)


db.close()
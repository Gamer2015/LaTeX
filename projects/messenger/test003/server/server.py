import database
import websocket

dbFileName = 'test001.db'
serverName = 'localhost'
socketPort = 8080

database.init(dbFileName)
websocket.init(serverName, socketPort, dbFileName)
import database
import websocket

dbFileName = 'test001.db'
database.init(dbFileName)

websocket.init('localhost', 8080, dbFileName) 

def dbBinary2hex(dbBinary):
  return dbBinary[::-1].hex()

def fn(data):
	channels = data["channels"];
	for channel in channels:
		channel["id"] = bytes.fromhex(channel["id"])

data = {'channels':[{'id':'01234567'}]}
print(data);
fn(data)
print(data);


import secrets
import bcrypt
idLength = 8
#id = bytes.fromhex('000000001')  

#print(id)
#print(id.hex().lstrip('00'))
#print(dbBinary2hex(id))

"""
count = []
for i in range(100000):
	id =  secrets.token_bytes(idLength)	
	count = 1
	while id[0] == 0:
		print(id)
		id =  secrets.token_bytes(idLength)
		count = count+1

	if(count > 1):
		print(i, count)"""

friends = ['Gabriel', 'Susanna', 'Philipp', 'Christoph', 'Lukas']
otherFriends = ['Alex', 'Linda', 'Nina', 'Linda', 'Linda']
friends.extend(otherFriends)
friends.append('Laura')
friends.insert( 0, 'Julia') 
friends.remove('Linda') # removes first instance

for friend in friends:
	print(friend)

for index in range(10):
	print(index)

for index in range(3,10):
	print(index)

for index in range(len(friends)):
	print(friends[index])


for index in range(10):
	if(index == 0):
		print("first Iteration")
	else:
		print("Not first iteration")
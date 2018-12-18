
print("Hello !");
# name = input("Enter your name: ")
# age = input("Enter your name: ")

# print("Hello " + name + "! You are " + age + " years old!")

friends = ['Gabriel', 'Susanna', 'Philipp', 'Christoph', 'Lukas']
otherFriends = ['Alex', 'Linda', 'Nina', 'Linda', 'Linda']
friends.extend(otherFriends)
friends.append('Laura')
friends.insert( 0, 'Julia') 
friends.remove('Linda') # removes first instance
lastfriend = friends.pop();

print(friends);
print(lastfriend);

print(friends.index('Alex'))
print(friends.count('Linda'))
sortedFriends = friends;
sortedFriends.sort()
sortedFriends.reverse();


copyList = friends.copy();
copyList[5] = 'Nobody'
print(copyList);
print(friends);
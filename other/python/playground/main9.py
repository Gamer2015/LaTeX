

def translate(string):
	translation = ""
	for letter in string:
		if letter.lower() in "aeiou":
			if letter.isupper():
				translation += 'G'
			else:
				translation += 'g'
		else:
			translation += letter
	return translation

while True:
	print(translate(input("Insert a Text:")))


# This is a comment
""" this is a 
multiline comment """
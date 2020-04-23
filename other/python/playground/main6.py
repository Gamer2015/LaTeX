

secret_code = "giraffe"
guess = "" 
guessingcount = 0
while (secret_code != guess and guessingcount <= 10):
	guess = input("Enter a guess:")
	guessingcount += 1

if(secret_code == guess):
	print("Gratulations!")	
else:
	print("Maybe next time!")
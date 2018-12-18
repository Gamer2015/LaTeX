""" Text """

def intinput(prompt):
	while True:
		try:
			number = int(input(prompt))
			return number
		except:
			print("This is not a number, try again")


# number = intinput("Give me a number: ")


try:
	value = 10/0
	number = int(input(prompt))
except ZeroDivisionError as err:
	print(err)
except ValueError as err:
	print(err)
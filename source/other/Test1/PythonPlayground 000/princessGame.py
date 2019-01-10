
# prompt for int
def intinput(prompt, minval=None, maxval=None, limit=-1):
	if minval > maxval:
		minval, maxval = maxval, minval

	while limit != 0:
		limit -= 1;
		try:
			number = int(input(prompt))

			mincon = (minval == None or number >= minval)
			maxcon = (maxval == None or number <= maxval)

			if(mincon and maxcon):
				return number
		except:
			if limit == 0:
				raise

def playGame(ndoors):
	doors 		= ['p' for i in range(ndoors)]
	defaultList	= [' ' for i in range(ndoors)]	

	running = doors.count('p') != 0
	while running == True:
		print(" " + " ".join([str(i) for i in range(ndoors)]))	
		print("|" + "|".join(doors) + "|")
		print("\n")
		pos = intinput("Where do you want to sleep?\n\nA: ", 0, ndoors - 1)

		doors[pos] 	= ' ';
		moreDoors 	= defaultList.copy()
		for index, door in enumerate(doors):
			if door == 'p':	
				if index != 0:
					moreDoors[index - 1] = 'p'
				if index != len(doors) - 1:
					moreDoors[index + 1] = 'p'

		doors = moreDoors
		running = doors.count('p') != 0


restart = True
while restart == True:
	ndoors 		= intinput("How many doors do you want to play with? (0 - 100)\n\nA: ", 100, 0)

	playGame(ndoors)

	print("\n\nCongratulations, you slept with the Princess!\n\n")
	restart_input = input("Do you want to restart? (y/n)\n\nA: ")
	print("\n\n")

	restart = restart_input == 'y'



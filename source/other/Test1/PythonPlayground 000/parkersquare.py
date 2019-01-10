from itertools import permutations, combinations

###

def take(n, gen, *args):
	g = gen(*args)
	return [next(g) for i in range(n)]

def generate(start, step=1, end=None):	
	value = start
	while end == None or value <= end:
		yield value
		value += step

def N():
	value = 1
	while True:
		yield value
		value += 1

###		

fields = 9
naturals = N();
stored 	= take(8, N)

done = False
count = 1
gk = generate(9)
while done == False:
	try:
		k = next(gk)
	except:
		break

	gc = combinations(stored, 8)
	stored.append(k)
	while done == False:
		try:
			comb = next(gc)
		except:
			break

		lst = [i**2 for i in comb]
		lst.append(k**2)
		print(sum(lst))

"""
		gp = permutations(lst, 9)
		while done == False:
			try:
				perm = next(gp)
			except:
				break

			p1, p2, p3, p4, p5, p6, p7, p8, p9 = perm
			sum = p1 + p2 + p3

			if (p4+p5+p6 == sum
				and p7+p8+p9 == sum
				and p1+p4+p7 == sum
				and p2+p5+p8 == sum
				and p3+p6+p9 == sum
				and p1+p5+p9 == sum
				and p3+p5+p7 == sum):
				print("Solved with:", perm)
				done = True



			if(count % 100000 == 0):
				print(count, perm)
			count += 1
"""


"""
1 2 3
4 5 6
7 8 9

1+2+3
4+5+6
7+8+9

1+4+7
2+5+8
3+6+9

1+5+9
3+5+7
"""
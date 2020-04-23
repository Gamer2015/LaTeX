from itertools import permutations, combinations
import math

###

def take(n, gen):
	return [next(gen) for i in range(n)]

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

def totalgen():
	i = 2
	while True:
		yield i**2*9
		i += 1

def removeBeginning(lst, k):
	minsum = k**2 + sum([i**2 for i in range(2,9)])
	lst = [x for x in lst if x > k**2]
	return lst

def addTotals(lst, gen, k):
	while True:
		val = next(gen);
		lst.append(val)
		maxsum = sum([(k-i)**2 for i in range(9)])
		if(val >= maxsum):
			return lst

###

fields = 9
generator = generate(2)
stored 	= take(8, generator)

totalGenerator = totalgen()
totals = []

done = False
count = 1

checkedCombs = 0
goodCombs = 0
for k in generator:
	totals = removeBeginning(totals, k)
	totals = addTotals(totals, totalGenerator, k)

	for comb in combinations(stored, fields-1):
		checkedCombs += 1
		lst = [i**2 for i in comb]
		lst.append(k**2)
		lstsum = sum(lst)
		nineth = lstsum / 9

		if lstsum in totals and any([x == nineth for x in lst]):
			goodCombs += 1				
			if(goodCombs % 1000 == 0):
				print("good:", goodCombs, "total:", checkedCombs)	
				print(totals, lstsum, lst)	

			permlst = [x for x in lst if x != nineth]
			p5 = nineth

			for perm in permutations(permlst):
				p1, p2, p3, p4, p6, p7, p8, p9 = perm
				lam = p1 + p2 + p3

				if (p4+p5+p6 == lam
					and p7+p8+p9 == lam
					and p1+p4+p7 == lam
					and p2+p5+p8 == lam
					and p3+p6+p9 == lam
					# and p1+p5+p9 == lam
					# and p3+p5+p7 == lam
					):
					print("Solved with:", perm)
					done = True

				if(count % 100000 == 0):
					print(count, perm)
				count += 1

	stored.append(k)
"""
				for perm in permutations(lst, 9):
					p1, p2, p3, p4, p5, p6, p7, p8, p9 = perm
					lam = p1 + p2 + p3

					if (p4+p5+p6 == lam
						and p7+p8+p9 == lam
						and p1+p4+p7 == lam
						and p2+p5+p8 == lam
						and p3+p6+p9 == lam
						and p1+p5+p9 == lam
						and p3+p5+p7 == lam):
						print("Solved with:", perm)
						done = True



					if(count % 100000 == 0):
						print(count, perm)
					count += 1
"""
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
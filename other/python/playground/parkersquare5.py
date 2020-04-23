import math

# finding possible A's

def N(dim, maxsum=None):
	total = dim
	if dim == 1:
		while maxsum == None or total <= maxsum:
			try:
				yield tuple([total])
			except GeneratorExit:
				return
			total += 1
	else: # dim >= 2
		while maxsum == None or total <= maxsum:
			for tup in N(dim - 1, total - 1):
				newTuple = [t for t in tup]
				value = sum(newTuple)
				newTuple.append(total - value)
				try:
					yield tuple(newTuple)
				except GeneratorExit:
					return
			total += 1

k = 0
for tup in N(3):
	lst = [x for x in tup]
	a,b,c = tup

	different = all([all(val1 != val2 for val2 in lst[index + 1:]) for index, val1 in enumerate(lst)])	
	if different and c**2 + b**2 - 2*a**2 == 0:
		print("solution:", (a,b,c))

	k += 1

	if k % 50000 == 0:
		print(k, tup)
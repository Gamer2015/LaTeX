import math

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

p = [0 for i in range(9)]

k = 0
for tup in N(5):
	a,b,c,d,e = tup
	a2 = a**2
	b2 = b**2
	c2 = c**2
	d2 = d**2
	lam = e**2 * 3

	absum = a+b
	diff = abs(a-b)

	p[-1+1] = int(b2 + d2 - c2)
	p[-1+2] = int(lam - b2 - d2)
	p[-1+3] = int(c2)
	p[-1+4] = int(a2 + c2 - d2)
	p[-1+5] = int(d2)
	p[-1+6] = int(lam - a2 - c2)
	p[-1+7] = int(lam - a2 - b2)
	p[-1+8] = int(b2)
	p[-1+9] = int(a2)

	try:
		squares = all([math.sqrt(x) % 1 == 0 for x in p])
		#different = all([all(val1 != val2 for val2 in p[index + 1:]) for index, val1 in enumerate(p)])
		same = sum([p[index+1:].count(val1) for index, val1 in enumerate(p)])

		if (squares):
			print("Same:", same, "Solved with:", p, (a,b,lam))
	except:
		pass

	k += 1

	if k % 50000 == 0:
		print(k, tup)
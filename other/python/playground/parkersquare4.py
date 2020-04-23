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
for n1, n2, n3 in N(3):
	a = n1**2
	b = n2**2
	lam = n3**2 * 3

	absum = a+b
	diff = abs(a-b)

	if(lam > absum
		and 3*absum > lam
		and lam > 3*diff):

		p[-1+1] = int(-a + 2*lam/3)
		p[-1+2] = int(a + b - 1*lam/3)
		p[-1+3] = int(-b + 2*lam/3)
		p[-1+4] = int(a - b + 1*lam/3)
		p[-1+5] = int(1*lam/3)
		p[-1+6] = int(-a + b + 1*lam/3)
		p[-1+7] = int(b)
		p[-1+8] = int(-a - b + lam)
		p[-1+9] = int(a)

		# different = all([all(val1 != val2 for val2 in p[index + 1:]) for index, val1 in enumerate(p)])
		squares = all([math.sqrt(x) % 1 == 0 for x in p])

		if (squares # different and 
			and p[-1+4]+p[-1+5]+p[-1+6] == lam
			and p[-1+7]+p[-1+8]+p[-1+9] == lam
			and p[-1+3]+p[-1+4]+p[-1+7] == lam
			and p[-1+2]+p[-1+5]+p[-1+8] == lam
			and p[-1+3]+p[-1+6]+p[-1+9] == lam
			and p[-1+3]+p[-1+5]+p[-1+9] == lam
			and p[-1+3]+p[-1+5]+p[-1+7] == lam):
			print("Solved with:", p, (a,b,lam))

		k += 1

		if k % 50000 == 0:
			print(k, p)
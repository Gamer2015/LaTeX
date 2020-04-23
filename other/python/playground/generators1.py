


def RN(start):
	value = start
	while(value > 0):
		try:
			yield value
		except GeneratorExit:
			return
		value -= 1

def N():
	value = 1
	while True:
		yield value
		value += 1

"""
def N2():
	k = 1
	v1 = 1
	v2 = 1
	while True:
		yield (v1, v2)
		v1 -= 1
		if v1 == 0:
			k += 1
			v1 = k
			v2 = 1
		else:
			v2 += 1

def _RN2(start):
	pass

def _N2():
	k = 1
	g1 = RN(k)
	g2 = N()
	while True:
		try:
			v1 = next(g1)
			v2 = next(g2)
			yield (v1, v2)
		except:
			k += 1
			g1 = RN(k)
			g2 = N()
"""
"""
def N(dim): # works kinda for any countable sets
	k = 1
	if dim == 1:
		while True:
			try:
				yield k
			except GeneratorExit:
				return
			k += 1
	else:	
		g1 = RN(k)
		g2 = N(dim - 1)
		while True:
			try:
				v1 = next(g1)
				v2 = next(g2)
				try:
					yield (v2, v1)
				except GeneratorExit:
					return
			except:
				k += 1
				g1 = RN(k)
				g2 = N(dim - 1)
"""

def _N(dim, maxsum=None):
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
for i in N(2):
	k += 1
	print(i, k)

	if k == 50000:
		break



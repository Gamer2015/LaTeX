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
for i in N(4,6):
	print(i)
	k += 1
	if k >= 100000:
		break

"""
3: 1 + 2 + 3 + 4 
4: 1 + 4 + 10
"""


infinite, comb
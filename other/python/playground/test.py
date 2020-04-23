import itertools

k = 0
for i in itertools.product(N, repeat=5):
	print(i)
	k += 1
	if k >= 5000:
		break
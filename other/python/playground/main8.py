

def power(base, exponent):
	result = 1
	for i in range(exponent):
		result *= base
	return result

base = 8;
print(power(base, 3))

print(base)

grid = [
	[1,2,3],
	[4,5,6],
	[6,7,8]
]

print(grid[0][2])
for row in grid:
	for cell in row:
		print(cell)
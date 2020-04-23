import sys
import time

import numpy as np



# a = np.arange(15).reshape(3, 5)
# print(a)

# print(a.shape)

# a = np.array([1,2,3])
# b = np.array((1,2,3))

# print(a)
# print(b)
# print(a == b)

size = 1000

L1 = range(size)
L2 = range(size)

A1 = np.arange(size)
A2 = np.arange(size)

start = time.time()

result = [x+y for x,y in zip(L1, L2)]

print((time.time() - start) * 1000)

start = time.time()

result = A1 + A2

print((time.time() - start) * 1000)
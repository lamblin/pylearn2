from pylearn3.data.cache import LRUCache


def show(x):
    for z in x:
        print z,
    print
    print

import random
b = LRUCache(5)

for i in xrange(10):
    b[i] = random.random()

show(b)
b.invalidate(3)
b[3] = 0
show(b)
b[12] = 0
b[13] = 0
show(b)
print (12 in b)

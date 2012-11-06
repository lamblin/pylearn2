# -*- coding: utf-8 -*-

from pylearn3.data import backends
from pylearn3.data import datasources


def test():

    x = backends.CSVBackend("example-data/latency.csv")

    #print x[3:5:-2]
    print x.description()

    c=0
    for b in x.batches(5):
        print len(b), b
        print
        c+=1
        if (c>10): break

    print len(x)   

    d = datasources.DataSource(x)

    c=0
    for b in d.batches(5):
        print len(b), b
        print
        c+=1
        if (c>10): break

    ##print d.gather([1,2,3,4,5])


if __name__=="__main__":
    test()

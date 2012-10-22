# -*- coding: utf-8 -*-


import datasources.datasource
import datasources.backends.csv_backend


def test():

    x=datasources.backends.csv_backend.CSVBackend("example-data/latency.csv")

    #print x[3:5:-2]
    print x.description()

    c=0
    for b in x.batches(5):
        print len(b), b
        print
        c+=1
        if (c>10): break

    print len(x)   

    d=datasources.datasource.DataSource(x)

    c=0
    for b in d.batches(5):
        print len(b), b
        print
        c+=1
        if (c>10): break

    ##print d.gather([1,2,3,4,5])


if __name__=="__main__":
    test()

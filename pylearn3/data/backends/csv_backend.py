# -*- coding: utf-8 -*-

import exceptions
import backend
import codecs
import csv
#from cache.lru_cache import LRUCache


class CSVBackend(backend.Backend):

    def __iter__(self):
        this_reader=csv.reader(open(self.filename,"rb"))
        if self.has_header:
            this_reader.next() # skip header
        for item in this_reader:
            yield [ x.decode("utf-8") for x in item ]

    def batches(self,batch_size=None):
        done=False
        this_reader=csv.reader(open(self.filename,"rb"))
        if self.has_header:
            this_reader.next() # skip header
        while not done:
            batch=[]
            size=batch_size if batch_size!=None else self.batch_size
            for i in xrange(size):
                try:
                    batch.append( [x.decode("utf-8") 
                                   for x in this_reader.next()])
                except:
                    done=True
                    break

            yield batch

    def gather(self,x):
        raise exceptions.NotImplementedError("Stream-Only")

    def scatter(self,x):
        raise exceptions.NotImplementedError("Read-Only")

    def __contains__(self, x):
        raise exceptions.NotImplementedError("Stream-only")

    def __getitem__(self, x):
        raise exceptions.NotImplementedError("Stream-only")

    def __setitem__(self, x):
        raise exceptions.NotImplementedError("Read-Only")

    def __delitem__(self, x):
        raise exceptions.NotImplementedError("Read-Only")

    def __len__(self):
        return sum(1 for r in csv.reader(open(self.filename,"rb")))

    def is_stream(self):
        return True

    def is_random_access(self):
        return False

    def is_readable(self):
        return True

    def is_writable(self):
        return False

    def description(self):
        return self.desc

    def __init__(self,
                 filename,
                 has_header=True,
                 batch_size=100):

        self.filename=filename
        self.batch_size=batch_size
        self.has_header=has_header

        # cromulent CSV files have first line
        # that enumerate the fields names
        this_reader=csv.reader(open(filename,'rb'))
        if self.has_header:
            self.desc=[ x.decode("utf_8_sig") for x in this_reader.next()]
        else:
            self.desc=[]

import exceptions
from pylearn3.data import cache
from pylearn3.data import backends


class DataSource:

    def __iter__(self):
        for i in self.backend:
            yield i

    def batches(self, batch, filter=None):
        for b in self.backend.batches(batch):
            yield b

    def gather_nt(self, items):
        """
        Performs a non-temporal gather-read from items (where items is an
        iterable of some sort yielding the keys to read) (reads bypassing
        the cache, leaving it un-affected)
        """
        # if bach is list-like (or iterable
        # but not infinite), we haveto gather
        # the elements indexed by the list
        # (would obviously not work on 
        # write-only or stream backends)
        #
        # raise NotIterable or something if
        # items is not iterator-like
        #
        if self.backend.is_readable():
            return self.backend.gather(items)
        else:
            raise exceptions.IOError("Not Redable")

    def gather(self,items):
        """
        Performs a gather-read from items (where items is an iterable of
        some sort yielding the keys to read) (reads affect the cache)
        """
        if self.backend.is_readable():
            z=self.backend.gather(items)
            if self.cache:
                for (i,z) in zip(items,z):
                    self.cache[i]=z
            else:
                # no cache, so no problems
                pass
        else:
            raise exceptions.IOError("Not Readable")
        

    def scatter_nt(self, items):
        """
        Performs a non-temporal scatter-write of items (where items is an
        iterable of some kind yielding tuple-like objects with first
        element taken as the key) (writes bypassing the cache, leaving it
        un-affected)
        """
        if self.backend.is_writable():
            self.backend.scatter(items)
        else:
            raise exceptions.IOError("Not Writable")


    def scatter(self,items):
        """
        Performs a scatter-write of items. (where items is an iterable of
        some sort yielding tuple-like objects with the first element taken
        as the key) (writes affect the cache)
        """
        if self.backend.is_writable():
            self.backend.scatter(items)
        else:
            raise exceptions.IOError("Not Writable")
        
        if self.cache:
            for i in items:
                self.cache[i[0]]=i[1:]
        else:
            # no cache, so no problems.
            pass


    def __setitem__(self,x,v):
        if self.backend.is_writable():
            if self.cache:
                self.cache[x]=v # may cause ejection
            self.backend[x]=v

    def __getitem__(self,x):
        if self.backend.is_readable():
            if self.cache:
                if x in self.cache:
                    return self.cache[x]
                else:
                    z=self.backend[x]
                    if self.cache:
                        self.cache[x]=z # may cause ejection
                    return z

    def prefetch(self):
        """
        Prefetches keys from the cache's (if any) prefetcher (if any).
        
        This is a default implementation that relies on
        a Prefetcher-derived class. If you want to do something
        fancier, provide an alternate implementation in the
        DataSource-derived class.
        """
        if self.cache:
            if self.cache.prefetcher:
                to_prefetch=self.cache.prefetcher.prefetch()
                if to_prefetch:
                    if self.backend.is_streaming:
                        items=self.backend.next(to_prefetch)
                    else:
                        # random-access
                        for p in to_prefetch:
                            self.cache[p]=self.backend[p]
                else:
                    # do nothing yet
                    pass
            else:
                # no prefetcher, so no prefetch
                pass
        else:
            # no cache, so no prefetch
            pass

    def __init__(self,
                 backend,
                 cache=None):

        self.backend=backend
        self.cache=cache


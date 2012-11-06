
import exceptions
import cache


class LRUCache(cache.Cache):
    """Implements a dictionary-like LRU Cache.

    The LRU (Least Recently Used) Policy calls
    for the ejection of the element in the cache
    that was used the further back in time.

    While the cache is not full, items are just
    added. When the cache is full and a new item
    is added, the least recently used item is
    ejected and replaced by the new item.

    Each time an item in the cache is read or
    written to, its timestamp gets refreshed and
    it becomes the most recently used item.
    """

    def _now(self):
        """Returns the current timestamp
        for the cache.
        """
        self.ts += 1
        return self.ts

    def size(self):
        """Returns max. cache size
        (while len returns the current
        number of items held by the
        cache).
        """
        return self.cache_size

    def __len__(self):
        """Returns the current number
        of items in the cache (while
        size() returns the maximum
        number of items held by the
        cache).
        """
        return len(self.items)

    def invalidate(self, key):
        """Invalidates (deletes) a specific
        entry (without write-back)
        """
        if key in self.items:
            del self.items[key]
            del self.timestamps[key]

    def invalidate_all(self):
        """Invalidates all entries in
        the cache (i.e., flushes
        everything, without write-back).
        """
        self.items = dict()
        self.timestamps = dict()

    def __iter__(self):
        """Yields an iterator-object to
        iterate over the cache items.

        Note: using the iterator will
        refresh timestamps of items
        iterated over.
        """
        for i in self.items:
            self.timestamps[i] = self._now()
            yield (i,
                   self.items[i],
                   self.timestamps[i])

    def __contains__(self, key):
        """Overloads operator in,
        returns True if the item corresponding
        to key is in the cache
        """
        return key in self.items

    def __setitem__(self, key, value):
        """Overloads the write operator[]

        If the item is in the cache, it
        refreshes its timestamp. If the
        item is not in the cache, and
        the cache is not full, it simply
        adds the item to the cache. If
        the cache is full, the least
        recently used item is ejected
        from the cache (with no-write
        back) and the new item inserted.
        """

        if ((not key in self.items) and
            (len(self.items) == self.cache_size)):
            # find oldest key (smallest ts)
            # and invalidate it
            k = min(self.timestamps, key=self.timestamps.get)
            self.invalidate(k)

        # here we have either ejected a old entry
        # or we are overwriting one that's already
        # in the cache
        #
        self.timestamps[key] = self._now()
        self.items[key] = value
        if self.prefetcher:
            self.prefetcher.add(key,cache.WRITE)

    def __getitem__(self, key):
        """Overloads the read operator[]

        If the item is in the cache,
        it refreshes its timestamp,
        or raises KeyError otherwise
        """
        if key in self.items:
            # refresh timestamp, if the key
            # is found,
            self.timestamps[key] = self._now()

            if self.prefetcher:
                self.prefetcher.add(key,cache.READ)

            return self.items[key]
        else:
            # or raise an error
            raise KeyError

    def __init__(self, 
                 cache_size=1000,
                 prefetcher=None):
        #super(LRUCache,self).__init__()

        self.cache_size = cache_size
        self.prefetcher = prefetcher
        self.ts = 0
        self.items = dict()
        self.timestamps = dict()

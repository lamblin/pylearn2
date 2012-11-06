
import exceptions


class Prefetcher:

    def add(self, key, mode):
        """
        Adds a key to the key snoop cache.

        Mode is either cache.READ or cache.WRITE,
        and determine whether the key was read from,
        or written to, the cache.
        """
        raise exceptions.NotImplementedError

    def prefetch(self):
        """
        returns a list of indexes/key to fetch next if the associated
        source is random-access,

        returns a number of items to read if the source is streaming,

        of None, if it's not time to prefetch (because of reasons).
        """
        raise exceptions.NotImplementedError

    def reset(self):
        """
        Resets history.
        """
        raise exceptions.NotImplementedError

    def __init__(self,
                 cachesize,
                 is_stream,
                 is_readable,
                 is_writable):
        """
        Initializes the prefetch policy with information from the
        associated datasource and cache. Ideally, a policy would be
        quite different whether the back-end is streaming, or if it
        supports random access.
        """
        pass

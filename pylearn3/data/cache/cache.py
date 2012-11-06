import exceptions


class Cache(object):
    """The cache interface.

    This class presents the interface of a dictionary-like
    cache object.

    To implement specific cache policies, you must subclass
    this class and add policy-specific code.
    """

    # "enums" that are passed to a prefetcher as
    # hints for read or write
    _READ = 0
    _WRITE = 1

    def size(self):
        """Returns max. cache size (while len returns the current number of
        items held by the cache).
        """
        raise exceptions.NotImplementedError

    def __len__(self):
        """Returns the current number of items in the cache (while size()
        returns the maximum number of items held by the cache).
        """
        raise exceptions.NotImplementedError

    def invalidate(self, key):
        """Invalidates (deletes) a specific entry (without write-back)
        """
        raise exceptions.NotImplementedError

    def invalidate_all(self):
        """Invalidates all entries in the cache (i.e., flushes everything,
        without write-back).
        """
        raise exceptions.NotImplementedError

    def __iter__(self):
        """Yields an iterator-object to iterate over the cache items.
        """
        raise exceptions.NotImplementedError

    def __contains__(self, key):
        """Returns True if the item is in the cache."""
        raise exceptions.NotImplementedError

    def __setitem__(self, key, value):
        """Overloads the write operator[]

        If the item is in the cache, it refreshes its timestamp. If the
        item is not in the cache, and the cache is not full, it simply adds
        the item to the cache. If the cache is full, the policy-defined
        item is ejected from the cache (with no-write back) and the new
        item inserted.
        """
        raise exceptions.NotImplementedError

    def __getitem__(self, key):
        """Overloads the read operator[]

        If the item is in the cache,
        it refreshes its timestamp,
        or raises KeyError otherwise
        """
        raise exceptions.NotImplementedError

    def prefetch(self):
        """
        Gives a list of indexes/keys to prefetch given past read/write
        cache activity if the back-end is random access, or the number of
        items to prefetch if the back-end is streaming, or None if nothing
        is to be prefetched

        It's up to the datasource (or whatever object using the cache) to
        prefetch the items (possibly in another thread).

        Hooks must monitor indexes/keys (that go through __getitem__ and
        __setitem__) and feed them to the prefetch_policy class, so that it
        can suggest what to load next.
        """
        raise exceptions.NotImplementedError

    def __init__(self, cachesize, prefetcher=None):
        """
        creates a cache of cachesize entries, using a prefetcher (which can
        be None, in which case we do not have a pretecher)
        """
        pass

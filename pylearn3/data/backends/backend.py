# -*- coding: utf-8 -*-

import exceptions


class Backend:
    """
    The backend base class publishes the interface a basic backend must
    sport.

    In an most unpythonèsque way, this class uses virtual members that will
    throw NotImplementedError, forcing people to implement them in the
    derived classes.

    The backend has to behave (mostly) like a generic Python Container:

    __getitem__, __setitem__, and __delitems__ must support integers and
    slice objects,

    and return iterator-like objects (and not copies)

    possibly raises IndexError (bad index), TypeError (bad index type),
    KeyError (if dictionary-like and key does not exist)
    """

    def __iter__(self):
        """
        This function returns an iterator object on the collection
        """
        raise exceptions.NotImplementedError

    def batches(self):
        """
        This function returns a 'batch' of data (datasource-specific)
        """
        raise exceptions.NotImplementedError

    def next(self, n=1):
        """
        If the source is streaming, returns the next n (defaults to 1)
        items in the source.
        """
        raise exceptions.NotImplementedError

    def gather(self, items_index):
        """
        Performs a gather-read: returns a list of objects
        indexed by items_index, read from the data source.

        x.gather([2,5,7]) would return a list of the 3nd,
        6th, and 8th items.

        items_index therefore must be an iterable (but not
        necessarily sorted).
        """
        raise exceptions.NotImplementedError

    def scatter(self, items_tuples):
        """
        Perform a scatter-write: writes the objects at
        positions indexed by the first member of the
        tuple-like objects.

        x.scatter([(2,a),(5,b),(7,c)] would write a at
        position 2, b at position 5, and c at position 7.

        items_tuples must be an iterable of tuple-like objects.
        """
        raise exceptions.NotImplementedError

    def __contains__(self, x):
        """
        This function determines whether or not (at least one) x is in the
        collection.
        """
        raise exceptions.NotImplementedError

    def __getitem__(self, x):
        """
        This function returns either a single item, or an iterator object
        on the collection, if it's a slice-expression instead of an index
        """
        raise exceptions.NotImplementedError

    def __setitem__(self, x):
        """
        This function sets either a single item, or a range using an
        iterator object if it's a slice
        """
        raise exceptions.NotImplementedError

    def __delitem__(self, x):
        """
        Deletes an item or a range of items (if the argument is a slice)
        """
        raise exceptions.NotImplementedError

    def __len__(self):
        """
        Returns the size of the collection
        """
        raise exceptions.NotImplementedError

    def is_stream(self):
        """
        returns whether or not the backend is a read-only,
        streaming, source (i.e., does not support seeks nor
        write operations).
        """
        raise exceptions.NotImplementedError

    def is_random_access(self):
        """
        returns whether or not the backend supports arbitrary
        indexing of items.
        """
        raise exceptions.NotImplementedError

    def is_writable(self):
        """
        returns whether or not the backend accepts write operations
        """
        raise exceptions.NotImplementedError

    def is_readable(self):
        """
        returns whether or not the backend accepts write opetations
        """
        raise exceptions.NotImplementedError

    def description(self):
        """
        Returns a description of the data source
        """
        raise exceptions.NotImplementedError

    def __init__(self):
        pass

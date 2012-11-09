# -*- coding: utf-8 -*-
import numpy

import backend


class NdarrayBackend(backend.Backend):
    """
    Implementation of Backend where the data is in an ndarray in memory.

    Keys are the indices along the first (left-most) dimension of
    the array.

    It suppords random read/write operations.
    """

    def __init__(self, data, batch_size=100):
        # The data could be in a subclass of ndarray,
        # such as memmap.
        self.data = numpy.asanyarray(data)
        self.batch_size = batch_size

        self.ndim = self.data.ndim
        self.shape = self.data.shape
        self.dtype = self.data.dtype

    def __iter__(self):
        for sub_array in self.data:
            yield sub_array

    def batches(self, batch_size=None):
        if batch_size is not None:
            size = self.batch_size
        else:
            size = batch_size

        for i in xrange(0, len(self.data), size):
            yield self.data[(i * size):(i + 1) * size]

    def gather(self, items_index):
        # Simply uses advanced indexing
        return self.data[items_index]

    def scatter(self, items_tuples):
        # Build a tuple containing all keys, and one containing values
        keys, values = zip(*items_tuples)

        # Then, use advanced indexing (which requires lists or arrays,
        # not tuples, as indices)
        self.data[list(keys)] = values

    def __contains__(self, x):
        # I'm not sure what we should return. Is x a key (index) or value?
        raise NotImplementedError
        return 0 <= x < len(self.data)

    def __getitem__(self, x):
        # TODO: should there be a lazy iterator instead?
        return self.data[x]

    def __setitem__(self, x, v):
        self.data[x] = v

    def __delitem__(self, x):
        raise TypeError("Cannot delete elements")

    def __len__(self):
        return len(self.data)

    def is_stream(self):
        return False

    def is_random_access(self):
        return True

    def is_readable(self):
        return True

    def is_writable(self):
        return True

    def description(self):
        # TODO: not sure what to put here.
        raise NotImplementedError
        # Nested lists containing "dtype" with the same shape as an example?
        return 'ndarray of rank %i, shape: %s, dtype: %s' % (
                self.ndim, self.shape, self.dtype)

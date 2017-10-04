#!/usr/bin/env python

# Copyright 2017 DIANA-HEP
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import json
import math

class Proxy(object):
    def toJsonString(self):
        return json.dumps(self.toJson())

################################################################ list proxy

class ListProxy(list, Proxy):
    __slots__ = ["__oam", "__index"]

    def __init__(self, oam, index):
        self.__oam = oam
        self.__index = index

    def __repr__(self):
        dots = ", ..." if len(self) > 4 else ""
        return "[{0}{1}]".format(", ".join(map(repr, self[:4])), dots)

    def __len__(self):
        return int(self.__oam.endarray[self.__index] - self.__oam.startarray[self.__index])

    def __getitem__(self, index):
        if isinstance(index, slice):
            return sliceofproxy(self, index)
        else:
            index = normalizeindex(self, index, False, 1)
            return self.__oam.contents.proxy(self.__oam.startarray[self.__index] + index)

    def __getslice__(self, start, stop):
        # for old-Python compatibility
        return self.__getitem__(slice(start, stop))
    
    def __iter__(self):
        if sys.version_info[0] <= 2:
            return (self[i] for i in xrange(len(self)))
        else:
            return (self[i] for i in range(len(self)))

    def append(self, *args, **kwds):       raise TypeError("ListProxy is immutable (cannot be changed in-place)")
    def __delitem__(self, *args, **kwds):  raise TypeError("ListProxy is immutable (cannot be changed in-place)")
    def __delslice__(self, *args, **kwds): raise TypeError("ListProxy is immutable (cannot be changed in-place)")
    def extend(self, *args, **kwds):       raise TypeError("ListProxy is immutable (cannot be changed in-place)")
    def __iadd__(self, *args, **kwds):     raise TypeError("ListProxy is immutable (cannot be changed in-place)")
    def __imul__(self, *args, **kwds):     raise TypeError("ListProxy is immutable (cannot be changed in-place)")
    def insert(self, *args, **kwds):       raise TypeError("ListProxy is immutable (cannot be changed in-place)")
    def pop(self, *args, **kwds):          raise TypeError("ListProxy is immutable (cannot be changed in-place)")
    def remove(self, *args, **kwds):       raise TypeError("ListProxy is immutable (cannot be changed in-place)")
    def reverse(self, *args, **kwds):      raise TypeError("ListProxy is immutable (cannot be changed in-place)")
    def __setitem__(self, *args, **kwds):  raise TypeError("ListProxy is immutable (cannot be changed in-place)")
    def __setslice__(self, *args, **kwds): raise TypeError("ListProxy is immutable (cannot be changed in-place)")
    def sort(self, *args, **kwds):         raise TypeError("ListProxy is immutable (cannot be changed in-place)")

    def __add__(self, other): return list(self) + list(other)
    def __mul__(self, reps): return list(self) * reps
    def __rmul__(self, reps): return reps * list(self)
    def __reversed__(self):
        if sys.version_info[0] <= 2:
            return (self[i - 1] for i in xrange(len(self), 0, -1))
        else:
            return (self[i - 1] for i in range(len(self), 0, -1))
    def count(self, value): return sum(1 for x in self if x == value)
    def index(self, value, *args):
        if len(args) == 0:
            start = 0
            stop = len(self)
        elif len(args) == 1:
            start = args[0]
            stop = len(self)
        elif len(args) == 2:
            start, stop = args
        else:
            raise TypeError("index() takes at most 3 arguments ({0} given)".format(1 + len(args)))
        for i, x in enumerate(self):
            if x == value:
                return i
        raise ValueError("{0} is not in list".format(value))

    def __contains__(self, value):
        for x in self:
            if x == value:
                return True
        return False

    def __hash__(self):
        return hash(tuple(self))

    def __eq__(self, other):
        return isinstance(other, list) and len(self) == len(other) and all(x == y for x, y in zip(self, other))

    def __lt__(self, other):
        if isinstance(other, ListProxy):
            return list(self) < list(other)
        elif isinstance(other, list):
            return list(self) < other
        else:
            raise TypeError("unorderable types: {0} < {1}".format(self.__class__, other.__class__))

    def __ne__(self, other): return not self.__eq__(other)
    def __le__(self, other): return self.__lt__(other) or self.__eq__(other)
    def __gt__(self, other):
        if isinstance(other, ListProxy):
            return list(self) > list(other)
        else:
            return list(self) > other
    def __ge__(self, other): return self.__gt__(other) or self.__eq__(other)

    def toJson(self):
        return [toJson(x) for x in self]

################################################################ list slice proxy

class ListSliceProxy(ListProxy):
    __slots__ = ["__listproxy", "__start", "__stop", "__step"]

    def __init__(self, listproxy, start, stop, step):
        self.__listproxy = listproxy
        self.__start = start
        self.__stop = stop
        self.__step = step

    @property
    def __oam(self):
        return self.__listproxy.__oam

    def __len__(self):
        if self.__step == 1:
            return self.__stop - self.__start
        else:
            return int(math.ceil(float(self.__stop - self.__start) / self.__step))

    def __getitem__(self, index):
        if isinstance(index, slice):
            return sliceofproxy(self, index)
        else:
            return self.__listproxy[self.__start + self.__step*normalizeindex(self, index, False, 1)]

################################################################ record proxy superclass

class RecordProxy(Proxy):
    __slots__ = ["__oam", "__index"]

    def __init__(self, oam, index):
        self.__oam = oam
        self.__index = index

    def __repr__(self):
        return "<{0} at index {1}>".format(self.__class__.__name__, self.__index)

    def __eq__(self, other):
        return isinstance(other, RecordProxy) and set(self.__oam.contents.keys()) == set(other.__oam.contents.keys()) and all(getattr(self, name) == getattr(other, name) for name in self.__oam.contents.keys())

    def __lt__(self, other):
        if isinstance(other, RecordProxy):
            if len(self.__oam.contents) > len(other.__oam.contents):
                return True

            elif len(self.__oam.contents) < len(other.__oam.contents):
                return False

            elif set(self.__oam.contents.keys()) == set(other.__oam.contents.keys()):
                return tuple(getattr(self, name) for name in self.__oam.contents.keys()) < tuple(getattr(other, name) for name in other.__oam.contents.keys())

            else:
                return sorted(self.__oam.contents.keys()) == sorted(other.__oam.contents.keys())

        else:
            raise TypeError("unorderable types: {0} < {1}".format(self.__class__, other.__class__))
    def __ne__(self, other): return not self.__eq__(other)
    def __le__(self, other): return self.__lt__(other) or self.__eq__(other)
    def __gt__(self, other):
        if isinstance(other, LazyRecord):
            return list(self) > list(other)
        else:
            return list(self) > other
    def __ge__(self, other): return self.__gt__(other) or self.__eq__(other)

    def toJson(self):
        return dict((name, toJson(getattr(self, name))) for name in self.__oam.contents)

################################################################ tuple proxy

class TupleProxy(tuple, Proxy):
    __slots__ = ["__oam", "__index"]

    def __init__(self, oam, index):
        self.__oam = oam
        self.__index = index

    def __repr__(self):
        return "({0})".format(", ".join(repr(x) for x in self))

    def __len__(self):
        return len(self.__oam.contents)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return tuple(self[i] for i in range(len(self.__oam.contents))[index])
        else:
            return self.__oam.contents[index].proxy(self.__index)

    def __getslice__(self, start, stop):
        # for old-Python compatibility
        return self.__getitem__(slice(start, stop))

    def __iter__(self):
        return (self[i] for i in range(len(self)))

    def __add__(self, other): return tuple(self) + tuple(other)
    def __mul__(self, reps): return tuple(self) * reps
    def __rmul__(self, reps): return reps * tuple(self)
    def __reversed__(self):
        if sys.version_info[0] <= 2:
            return (self[i - 1] for i in xrange(len(self), 0, -1))
        else:
            return (self[i - 1] for i in range(len(self), 0, -1))
    def count(self, value): return sum(1 for x in self if x == value)
    def index(self, value, *args):
        if len(args) == 0:
            start = 0
            stop = len(self)
        elif len(args) == 1:
            start = args[0]
            stop = len(self)
        elif len(args) == 2:
            start, stop = args
        else:
            raise TypeError("index() takes at most 3 arguments ({0} given)".format(1 + len(args)))
        for i, x in enumerate(self):
            if x == value:
                return i
        raise ValueError("{0} is not in tuple".format(value))

    def __contains__(self, value):
        for x in self:
            if x == value:
                return True
        return False

    def __hash__(self):
        return hash(tuple(self))

    def __eq__(self, other):
        return isinstance(other, tuple) and len(self) == len(other) and all(x == y for x, y in zip(self, other))

    def __lt__(self, other):
        if isinstance(other, TupleProxy):
            return tuple(self) < tuple(other)
        elif isinstance(other, list):
            return tuple(self) < other
        else:
            raise TypeError("unorderable types: {0} < {1}".format(self.__class__, other.__class__))

    def __ne__(self, other): return not self.__eq__(other)
    def __le__(self, other): return self.__lt__(other) or self.__eq__(other)
    def __gt__(self, other):
        if isinstance(other, TupleProxy):
            return tuple(self) > tuple(other)
        else:
            return tuple(self) > other
    def __ge__(self, other): return self.__gt__(other) or self.__eq__(other)

    def toJson(self):
        return [toJson(x) for x in self]

################################################################ helper functions

def normalizeindex(listproxy, index, clip, step):
    lenproxy = len(listproxy)
    if index < 0:
        j = lenproxy + index
        if j < 0:
            if clip:
                return 0 if step > 0 else lenproxy
            else:
                raise IndexError("index out of range: {0} for length {1}".format(index, lenproxy))
        else:
            return j
    elif index < lenproxy:
        return index
    elif clip:
        return lenproxy if step > 0 else 0
    else:
        raise IndexError("index out of range: {0} for length {1}".format(index, lenproxy))

def sliceofproxy(listproxy, slice):
    if slice.step is None:
        step = 1
    else:
        step = slice.step
    if step == 0:
        raise ValueError("slice step cannot be zero")

    lenproxy = len(listproxy)
    if lenproxy == 0:
        return ListSliceProxy(listproxy, 0, 0, 1)

    if slice.start is None:
        if step > 0:
            start = 0
        else:
            start = lenproxy - 1
    else:
        start = normalizeindex(listproxy, slice.start, True, step)

    if slice.stop is None:
        if step > 0:
            stop = lenproxy
        else:
            stop = -1
    else:
        stop = normalizeindex(listproxy, slice.stop, True, step)

    return ListSliceProxy(listproxy, start, stop, step)

def mapsto(proxy, byname=True):
    oam = proxy.__oam
    if byname:
        while oam.base is not None:
            oam = oam.base
    return proxy.__index, oam

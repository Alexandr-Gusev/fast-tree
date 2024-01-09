from collections.abc import MutableMapping
from threading import Lock
from bisect import bisect
from fast_tree_utils import get_block


class ObservableDict(MutableMapping):
    def __init__(self, add, remove, data):
        super(self.__class__, self).__init__()
        self.__add = lambda container, key, value: value
        self.update(data)
        self.__add = add
        self.__remove = remove

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = self.__add(self, key, value)

    def __delitem__(self, key):
        del self.__dict__[key]
        self.__remove(self, key)

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)


class FastTree(object):
    def __init__(self, key, key_for_sorting, key_for_search):
        super(self.__class__, self).__init__()

        self.__key = key
        self.__key_for_sorting = key_for_sorting
        self.__key_for_search = key_for_search

        self.__mutex = Lock()

        self.__items = ObservableDict(self.__add, self.__remove, {})
        self.__groups = ObservableDict(self.__add, self.__remove, {})

        self.__rows = []
        self.__keys_for_sorting = []
        self.__keys_for_search = []

        self.__index_by_key = {}

    def __add(self, container, key, value):
        with self.__mutex:
            key_for_sorting = self.__key_for_sorting(value)
            key_for_search = self.__key_for_search(value)

            index = self.__index_by_key.pop(key, None)
            if index is not None:
                if key_for_sorting == self.__keys_for_sorting[index]:
                    return self.__rows[index]

                self.__rows.pop(index)
                self.__keys_for_sorting.pop(index)
                self.__keys_for_search.pop(index)

            index = bisect(self.__keys_for_sorting, key_for_sorting)
            self.__index_by_key[key] = index

            item = value if isinstance(value, ObservableDict) else ObservableDict(self.__edit, self.__edit, value)

            self.__rows.insert(index, item)
            self.__keys_for_sorting.insert(index, key_for_sorting)
            self.__keys_for_search.insert(index, key_for_search)

            return item

    def __remove(self, container, key):
        with self.__mutex:
            index = self.__index_by_key.pop(key, None)
            if index is not None:
                self.__rows.pop(index)
                self.__keys_for_sorting.pop(index)
                self.__keys_for_search.pop(index)

    def __edit(self, container, key, value):
        self.__add(None, self.__key(container), container)
        return value

    def items(self):
        return self.__items

    def groups(self):
        return self.__groups

    def get_block(self, block_size, block_start, query, thread_count=0, min_rows_per_thread=1000):
        with self.__mutex:
            return get_block(self.__rows, self.__keys_for_search, block_size, block_start, query, thread_count, min_rows_per_thread)

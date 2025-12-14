from collections.abc import MutableMapping
from threading import Lock
from bisect import bisect
from fast_tree_utils import get_block


class FastTreeDict(MutableMapping):
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
    def __init__(self, key_property, group_key_property, key_for_sorting, key_for_search):
        super(self.__class__, self).__init__()

        self.__key_property = key_property
        self.__group_key_property = group_key_property
        self.__key_for_sorting = key_for_sorting
        self.__key_for_search = key_for_search

        self.__key_for_sorting_items = self.__create_key_for_sorting(False)
        self.__key_for_sorting_groups = self.__create_key_for_sorting(True)

        self.__add_item = self.__create_add(False)
        self.__add_group = self.__create_add(True)

        self.__remove_item = self.__create_remove(False)
        self.__remove_group = self.__create_remove(True)

        self.__mutex = Lock()

        self.__items = FastTreeDict(self.__add_item, self.__remove_item, {})
        self.__groups = FastTreeDict(self.__add_group, self.__remove_group, {})

        self.__rows = []
        self.__keys_for_sorting = []
        self.__keys_for_search = []

        self.__index_by_key = {}

    def __create_key_for_sorting(self, group):
        prefix_for_sorting = not group

        def key_for_sorting(item):
            if self.__group_key_property is None:
                return self.__key_for_sorting(item)

            res = [prefix_for_sorting, self.__key_for_sorting(item)]
            group_key = item[self.__group_key_property]
            if group_key is None:
                return res
            group = self.__groups[group_key]
            return self.__key_for_sorting_groups(group) + res

        return key_for_sorting

    def __create_add(self, group):
        __key_for_sorting = self.__key_for_sorting_groups if group else self.__key_for_sorting_items
        edit_ref = []

        def add(container, key, value):
            with self.__mutex:
                key = group, key
                key_for_sorting = __key_for_sorting(value)
                key_for_search = self.__key_for_search(value)

                index = self.__index_by_key.pop(key, None)
                if index is not None:
                    if key_for_sorting == self.__keys_for_sorting[index]:
                        return self.__rows[index]

                    if group:
                        count = 1

                        group_rows = self.__rows[index:index + count]
                        group_keys_for_sorting = self.__keys_for_sorting[index:index + count]
                        group_keys_for_search = self.__keys_for_search[index:index + count]

                        self.__rows = self.__rows[:index] + self.__rows[index + count]
                        self.__keys_for_sorting = self.__keys_for_sorting[:index] + self.__keys_for_sorting[index + count]
                        self.__keys_for_search = self.__keys_for_search[:index] + self.__keys_for_search[index + count]
                    else:
                        self.__rows.pop(index)
                        self.__keys_for_sorting.pop(index)
                        self.__keys_for_search.pop(index)

                index = bisect(self.__keys_for_sorting, key_for_sorting)
                self.__index_by_key[key] = index

                item = value if isinstance(value, FastTreeDict) else FastTreeDict(edit_ref[0], edit_ref[0], value)

                if group:
                    self.__rows = self.__rows[:index] + group_rows + self.__rows[index + count]
                    self.__keys_for_sorting = self.__keys_for_sorting[:index] + group_keys_for_sorting + self.__keys_for_sorting[index + count]
                    self.__keys_for_search = self.__keys_for_search[:index] + group_keys_for_search + self.__keys_for_search[index + count]
                else:
                    self.__rows.insert(index, item)
                    self.__keys_for_sorting.insert(index, key_for_sorting)
                    self.__keys_for_search.insert(index, key_for_search)

                return item

        def edit(container, key, value):
            add(None, container[self.__key_property], container)
            return value

        edit_ref.append(edit)

        return add

    def __create_remove(self, group):
        def remove(container, key):
            with self.__mutex:
                key = group, key
                index = self.__index_by_key.pop(key, None)
                if index is not None:
                    if group:
                        count = 1
                        self.__rows = self.__rows[:index] + self.__rows[index + count]
                        self.__keys_for_sorting = self.__keys_for_sorting[:index] + self.__keys_for_sorting[index + count]
                        self.__keys_for_search = self.__keys_for_search[:index] + self.__keys_for_search[index + count]
                    else:
                        item = self.__rows.pop(index)
                        self.__keys_for_sorting.pop(index)
                        self.__keys_for_search.pop(index)

        return remove

    def items(self):
        return self.__items

    def groups(self):
        return self.__groups

    def get_block(self, block_size, block_start, query, expanded_group_keys=[], thread_count=0, min_rows_per_thread=1000):
        with self.__mutex:
            return get_block(self.__rows, self.__keys_for_search, block_size, block_start, query, thread_count, min_rows_per_thread)

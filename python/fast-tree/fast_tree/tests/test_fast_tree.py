import pytest
from ..fast_tree import FastTree


@pytest.mark.parametrize("thread_count", (1, 2))
def test_table(thread_count):
    def key_for_sorting(item):
        return item["name"], item["id"]

    def key_for_search(item):
        return "\t".join((item["name"], item["comment"]))

    tree = FastTree("id", None, key_for_sorting, key_for_search)
    items = tree.items()

    def add(item):
        items[item["id"]] = item

    add({"id": "2", "name": "item 1", "comment": "", "extra": "20"})
    add({"id": "1", "name": "item 1", "comment": "", "extra": "10"})
    add({"id": "4", "name": "item 4", "comment": "33", "extra": "40"})
    add({"id": "3", "name": "item 3", "comment": "", "extra": "30"})
    add({"id": "5", "name": "item 5", "comment": "33", "extra": "50"})

    def assert_block(block_size, block_start, query, expected_ids, expected_total):
        block = tree.get_block(block_size, block_start, query, [], thread_count, 2)
        rows = block["rows"]
        assert len(rows) == len(expected_ids)
        assert block["total"] == expected_total
        for i, row in enumerate(rows):
            assert row["id"] == expected_ids[i]
            assert row["extra"] == str(int(expected_ids[i]) * 10)

    assert_block(4, 0, "", ("1", "2", "3", "4"), 5)
    assert_block(4, 1, "", ("2", "3", "4", "5"), 5)
    assert_block(10, 0, "", ("1", "2", "3", "4", "5"), 5)
    assert_block(10, 1, "", ("2", "3", "4", "5"), 5)

    assert_block(2, 0, "3", ("3", "4"), 3)
    assert_block(2, 1, "3", ("4", "5"), 3)
    assert_block(10, 0, "3", ("3", "4", "5"), 3)
    assert_block(10, 1, "3", ("4", "5"), 3)


@pytest.mark.parametrize("thread_count", (1, 2))
def test_tree(thread_count):
    def key_for_sorting(item):
        return item["name"], item["id"]

    def key_for_search(item):
        return "\t".join((item["name"], item["comment"]))

    tree = FastTree("id", "group_id", key_for_sorting, key_for_search)
    items = tree.items()
    groups = tree.groups()

    """
    root
    |
    +---g1
    |   +---g2
    |   |   +---g3
    |   |   +---i31
    |   |   +---i32
    |   +---i21
    |   +---i22
    +---i11
    +---i12
    """

    def add_group(group):
        groups[group["id"]] = group

    add_group({"id": "g1", "name": "group 1", "group_id": None, "comment": "", "extra": "10"})
    add_group({"id": "g2", "name": "group 2", "group_id": "g1", "comment": "", "extra": "20"})
    add_group({"id": "g3", "name": "group 3", "group_id": "g2", "comment": "", "extra": "30"})

    def add_item(item):
        items[item["id"]] = item

    add_item({"id": "i11", "name": "item 11", "group_id": None, "comment": "", "extra": "1100"})
    add_item({"id": "i12", "name": "item 12", "group_id": None, "comment": "", "extra": "1200"})
    add_item({"id": "i21", "name": "item 21", "group_id": "g1", "comment": "", "extra": "2100"})
    add_item({"id": "i22", "name": "item 22", "group_id": "g1", "comment": "", "extra": "2200"})
    add_item({"id": "i31", "name": "item 31", "group_id": "g2", "comment": "", "extra": "3100"})
    add_item({"id": "i32", "name": "item 32", "group_id": "g2", "comment": "", "extra": "3200"})

    def assert_block(block_size, block_start, query, expanded_group_keys, expected_ids, expected_total):
        block = tree.get_block(block_size, block_start, query, expanded_group_keys, thread_count, 2)
        rows = block["rows"]
        assert len(rows) == len(expected_ids)
        assert block["total"] == expected_total
        for i, row in enumerate(rows):
            assert row["id"] == expected_ids[i]
            assert row["extra"] == str(int(expected_ids[i][1:]) * (100 if expected_ids[i][0:1] == "i" else 10))

    assert_block(4, 0, "", [], ("g1", "g2", "g3", "i31"), 9)
    assert_block(4, 1, "", [], ("g2", "g3", "i31", "i32"), 9)
    assert_block(10, 0, "", [], ("g1", "g2", "g3", "i31", "i32", "i21", "i22", "i11", "i12"), 9)
    assert_block(10, 1, "", [], ("g2", "g3", "i31", "i32", "i21", "i22", "i11", "i12"), 9)

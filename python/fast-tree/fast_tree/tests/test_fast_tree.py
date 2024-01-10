import pytest
from ..fast_tree import FastTree


@pytest.mark.parametrize("thread_count", (1, 2))
def test_fast_tree(thread_count):
    def key(item):
        return item["id"]

    def key_for_sorting(item):
        return item["name"], item["id"]

    def key_for_search(item):
        return "\t".join((item["name"], item["comment"]))

    tree = FastTree(key, key_for_sorting, key_for_search)
    items = tree.items()

    def add(item):
        items[item["id"]] = item

    add({"id": "2", "name": "item 1", "comment": "", "extra": "20"})
    add({"id": "1", "name": "item 1", "comment": "", "extra": "10"})
    add({"id": "4", "name": "item 4", "comment": "33", "extra": "40"})
    add({"id": "3", "name": "item 3", "comment": "", "extra": "30"})
    add({"id": "5", "name": "item 5", "comment": "33", "extra": "50"})

    def assert_block(block_size, block_start, query, expected_ids, expected_total):
        block = tree.get_block(block_size, block_start, query, thread_count, 2)
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

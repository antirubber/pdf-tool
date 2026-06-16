from pdf_tool.widgets.reorder import apply_move


def test_apply_move_to_front():
    items = [1, 2, 3, 4]
    apply_move(items, 4, 1)
    assert items == [4, 1, 2, 3]


def test_apply_move_to_back():
    items = ["a", "b", "c"]
    apply_move(items, 1, 3)
    assert items == ["b", "c", "a"]


def test_apply_move_is_noop_for_same_position():
    items = [1, 2, 3]
    apply_move(items, 2, 2)
    assert items == [1, 2, 3]

from collections.abc import Callable
from typing import TypeVar

import questionary
from rich.console import Console
from rich.table import Table

_console = Console()

_T = TypeVar("_T")


def apply_move(items: list, from_pos: int, to_pos: int) -> None:
    """Move the item at 1-based ``from_pos`` to 1-based ``to_pos``, in place."""
    item = items.pop(from_pos - 1)
    items.insert(to_pos - 1, item)


def _show(items: list, label: Callable[[object], str]) -> None:
    table = Table(title="Current order", show_header=False)
    table.add_column("#")
    table.add_column("Item")
    for i, item in enumerate(items, start=1):
        table.add_row(str(i), label(item))
    _console.print(table)


def reorder_items(
    items: list[_T],
    *,
    label: Callable[[_T], str],
    done_label: str = "Looks good",
) -> list[_T] | None:
    """Interactively reorder a copy of ``items``.

    The move-an-item interaction shared by Merge (file order) and Reorder
    (page order). Returns the new order, or None if cancelled.
    """
    order = list(items)
    while True:
        _show(order, label)
        action = questionary.select(
            "Reorder?",
            choices=[
                questionary.Choice(done_label, value="done"),
                questionary.Choice("Move an item", value="move"),
                questionary.Choice("Cancel", value="cancel"),
            ],
        ).ask()
        if action is None or action == "cancel":
            return None
        if action == "done":
            return order

        def _in_range(v: str) -> bool | str:
            return (v.isdigit() and 1 <= int(v) <= len(order)) or (
                f"Enter 1..{len(order)}."
            )

        from_idx = questionary.text(
            f"Move which item (1..{len(order)})?", validate=_in_range
        ).ask()
        if from_idx is None:
            continue
        to_idx = questionary.text(
            f"Move to which position (1..{len(order)})?", validate=_in_range
        ).ask()
        if to_idx is None:
            continue
        apply_move(order, int(from_idx), int(to_idx))

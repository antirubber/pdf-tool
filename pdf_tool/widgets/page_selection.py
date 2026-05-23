import questionary

from pdf_tool.core.page_selection import (
    All,
    CustomRange,
    Even,
    FirstN,
    LastN,
    Odd,
    PageSelection,
)
from pdf_tool.core.range_parser import RangeParseError, parse_range


def _validate_range_spec(n_pages: int):
    def _validate(raw: str) -> bool | str:
        if not raw or not raw.strip():
            return "Range is required (e.g. 1-3,5,7-9)."
        try:
            parse_range(raw, n_pages=n_pages)
        except RangeParseError as e:
            return str(e)
        return True

    return _validate


def prompt_page_selection(n_pages: int) -> PageSelection | None:
    """Ask the user to pick a Page Selection for an N-page document.

    Returns the chosen PageSelection, or None on cancel.
    """
    choice = questionary.select(
        "Which pages?",
        choices=[
            questionary.Choice("All", value="all"),
            questionary.Choice("Odd", value="odd"),
            questionary.Choice("Even", value="even"),
            questionary.Choice("First N", value="first_n"),
            questionary.Choice("Last N", value="last_n"),
            questionary.Choice("Custom range (e.g. 1-3,5,7-9)", value="custom"),
        ],
    ).ask()
    if choice is None:
        return None
    if choice == "all":
        return All()
    if choice == "odd":
        return Odd()
    if choice == "even":
        return Even()
    if choice == "first_n":
        raw = questionary.text(
            "How many pages from the start?",
            validate=lambda v: v.isdigit() and int(v) >= 1 or "Enter a positive integer.",
        ).ask()
        if raw is None:
            return None
        return FirstN(n=int(raw))
    if choice == "last_n":
        raw = questionary.text(
            "How many pages from the end?",
            validate=lambda v: v.isdigit() and int(v) >= 1 or "Enter a positive integer.",
        ).ask()
        if raw is None:
            return None
        return LastN(n=int(raw))
    raw = questionary.text(
        f"Pages (1..{n_pages}):",
        validate=_validate_range_spec(n_pages),
    ).ask()
    if raw is None:
        return None
    return CustomRange(spec=raw)

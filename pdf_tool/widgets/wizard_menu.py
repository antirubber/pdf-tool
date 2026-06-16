from dataclasses import dataclass
from enum import Enum
from typing import Callable, Sequence

import questionary
from rich.align import Align
from rich.console import Group
from rich.panel import Panel
from rich.text import Text

from pdf_tool.core.probe import Available, BackendAvailability, BackendName


ACCENT = "cyan"


class OperationGroup(Enum):
    PROTECT = "Protect"
    INSPECT = "Inspect"
    TRANSFORM = "Transform"
    GENERATE = "Generate"


GROUP_ORDER: tuple[OperationGroup, ...] = (
    OperationGroup.PROTECT,
    OperationGroup.INSPECT,
    OperationGroup.TRANSFORM,
    OperationGroup.GENERATE,
)


@dataclass(frozen=True)
class MenuEntry:
    label: str
    value: str
    handler: Callable[[], None]
    backends: tuple[BackendName, ...]
    group: OperationGroup


WIZARD_STYLE = questionary.Style(
    [
        ("qmark", f"fg:{ACCENT} bold"),
        ("question", "bold"),
        ("pointer", f"fg:{ACCENT} bold"),
        ("highlighted", f"fg:{ACCENT} bold"),
        ("selected", f"fg:{ACCENT}"),
        # Group headers get the accent so they read as headers, distinct from
        # the dim, italic "unavailable" disabled rows.
        ("separator", f"fg:{ACCENT} bold"),
        ("disabled", "fg:#6c6c6c italic"),
    ]
)


def build_header(version: str) -> Panel:
    title = Text("pdf-tool", style=f"bold {ACCENT}")
    tagline = Text("Interactive wizard for everyday PDF tasks", style="dim")
    version_line = Align.right(Text(f"v{version}", style="dim"))
    body = Group(title, tagline, version_line)
    return Panel(body, border_style=ACCENT, padding=(0, 2))


def _choice_for(entry: MenuEntry, availability: BackendAvailability) -> questionary.Choice:
    missing = [b for b in entry.backends if not isinstance(availability[b], Available)]
    if len(missing) < len(entry.backends):
        return questionary.Choice(entry.label, value=entry.value)
    hints: list[str] = []
    for b in missing:
        status = availability[b]
        if not isinstance(status, Available):
            hints.append(status.install_hint)
    hint = " or ".join(hints) if hints else "missing backend"
    return questionary.Choice(
        entry.label, value=entry.value, disabled=f"unavailable — {hint}"
    )


def build_menu(
    operations: Sequence[MenuEntry],
    availability: BackendAvailability,
) -> list[questionary.Choice | questionary.Separator]:
    items: list[questionary.Choice | questionary.Separator] = []
    for group in GROUP_ORDER:
        members = [e for e in operations if e.group is group]
        if not members:
            continue
        items.append(questionary.Separator(f"\n  {group.value}"))
        for entry in members:
            items.append(_choice_for(entry, availability))
    return items

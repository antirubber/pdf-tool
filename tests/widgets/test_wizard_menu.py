from io import StringIO

import questionary
from rich.console import Console

from pdf_tool.core.probe import Available, BackendAvailability, BackendName, Missing
from pdf_tool.widgets.wizard_menu import (
    MenuEntry,
    OperationGroup,
    build_header,
    build_menu,
)


def _noop() -> None:
    pass


def _entries() -> tuple[MenuEntry, ...]:
    return (
        MenuEntry("Encrypt", "encrypt", _noop, (BackendName.PIKEPDF,), OperationGroup.PROTECT),
        MenuEntry("Decrypt", "decrypt", _noop, (BackendName.PIKEPDF,), OperationGroup.PROTECT),
        MenuEntry("Inspect", "inspect", _noop, (BackendName.PIKEPDF,), OperationGroup.INSPECT),
        MenuEntry("Rotate", "rotate", _noop, (BackendName.PIKEPDF,), OperationGroup.TRANSFORM),
        MenuEntry("Compress", "compress", _noop, (BackendName.GHOSTSCRIPT,), OperationGroup.TRANSFORM),
        MenuEntry("OCR", "ocr", _noop, (BackendName.OCRMYPDF,), OperationGroup.GENERATE),
    )


def _all_available() -> BackendAvailability:
    return {b: Available() for b in BackendName}


def _names(items) -> list[str]:
    out = []
    for item in items:
        if isinstance(item, questionary.Separator):
            out.append(f"SEP:{item.title.strip()}")
        else:
            out.append(item.title)
    return out


def test_menu_groups_appear_in_canonical_order():
    items = build_menu(_entries(), _all_available())
    names = _names(items)
    assert names == [
        "SEP:Protect",
        "Encrypt",
        "Decrypt",
        "SEP:Inspect",
        "Inspect",
        "SEP:Transform",
        "Rotate",
        "Compress",
        "SEP:Generate",
        "OCR",
    ]


def test_empty_groups_are_omitted():
    entries = tuple(e for e in _entries() if e.group is not OperationGroup.INSPECT)
    items = build_menu(entries, _all_available())
    names = _names(items)
    assert "SEP:Inspect" not in names
    assert "SEP:Protect" in names
    assert "SEP:Transform" in names


def test_missing_backend_produces_disabled_choice_with_install_hint():
    availability = _all_available()
    availability[BackendName.OCRMYPDF] = Missing(install_hint="brew install ocrmypdf")
    items = build_menu(_entries(), availability)
    ocr = next(i for i in items if not isinstance(i, questionary.Separator) and i.title == "OCR")
    assert ocr.disabled == "install: brew install ocrmypdf"


def test_choice_with_at_least_one_available_backend_is_enabled():
    entries = (
        MenuEntry(
            "Convert",
            "convert",
            _noop,
            (BackendName.LIBREOFFICE, BackendName.IMG2PDF),
            OperationGroup.GENERATE,
        ),
    )
    availability = _all_available()
    availability[BackendName.LIBREOFFICE] = Missing(install_hint="brew install libreoffice")
    items = build_menu(entries, availability)
    convert = next(i for i in items if not isinstance(i, questionary.Separator))
    assert convert.disabled is None
    assert convert.value == "convert"


def test_each_operation_appears_exactly_once():
    items = build_menu(_entries(), _all_available())
    labels = [i.title for i in items if not isinstance(i, questionary.Separator)]
    assert sorted(labels) == sorted({e.label for e in _entries()})
    assert len(labels) == len(set(labels))


def _rendered(panel) -> str:
    buf = StringIO()
    Console(file=buf, force_terminal=False, width=80).print(panel)
    return buf.getvalue()


def test_header_contains_name_tagline_and_version():
    out = _rendered(build_header("1.2.3"))
    assert "pdf-tool" in out
    assert "Interactive wizard for everyday PDF tasks" in out
    assert "v1.2.3" in out


def test_header_renders_for_dev_version_string():
    out = _rendered(build_header("0.0.1"))
    assert "v0.0.1" in out

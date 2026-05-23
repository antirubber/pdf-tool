from dataclasses import dataclass

from pdf_tool.core.range_parser import parse_range


@dataclass(frozen=True)
class All:
    pass


@dataclass(frozen=True)
class Odd:
    pass


@dataclass(frozen=True)
class Even:
    pass


@dataclass(frozen=True)
class FirstN:
    n: int


@dataclass(frozen=True)
class LastN:
    n: int


@dataclass(frozen=True)
class CustomRange:
    spec: str


PageSelection = All | Odd | Even | FirstN | LastN | CustomRange


def resolve(selection: PageSelection, n_pages: int) -> list[int]:
    match selection:
        case All():
            return list(range(1, n_pages + 1))
        case Odd():
            return list(range(1, n_pages + 1, 2))
        case Even():
            return list(range(2, n_pages + 1, 2))
        case FirstN(n):
            if n < 1:
                raise ValueError(f"FirstN requires n >= 1 (got {n})")
            return list(range(1, min(n, n_pages) + 1))
        case LastN(n):
            if n < 1:
                raise ValueError(f"LastN requires n >= 1 (got {n})")
            return list(range(max(1, n_pages - n + 1), n_pages + 1))
        case CustomRange(spec):
            return parse_range(spec, n_pages=n_pages)

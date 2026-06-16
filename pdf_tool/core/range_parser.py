class RangeParseError(ValueError):
    pass


def _parse_int(text: str, *, spec: str) -> int:
    try:
        n = int(text)
    except ValueError as e:
        raise RangeParseError(f"invalid page number {text!r} in range {spec!r}") from e
    if n < 1:
        raise RangeParseError(
            f"page numbers must be >= 1 (got {n} in range {spec!r})"
        )
    return n


def parse_range(spec: str, n_pages: int) -> list[int]:
    raw = spec
    spec = spec.strip()
    if not spec:
        raise RangeParseError("page range cannot be empty")
    pages: set[int] = set()
    for token in spec.split(","):
        token = token.strip()
        if not token:
            raise RangeParseError(f"empty token in range {raw!r}")
        if "-" in token:
            lo_str, hi_str = token.split("-", 1)
            lo = _parse_int(lo_str.strip(), spec=raw)
            hi = _parse_int(hi_str.strip(), spec=raw)
            if lo > hi:
                raise RangeParseError(
                    f"descending range {token!r} in {raw!r}: start must be <= end"
                )
            _check_upper_bound(hi, n_pages=n_pages, spec=raw)
            pages.update(range(lo, hi + 1))
        else:
            n = _parse_int(token, spec=raw)
            _check_upper_bound(n, n_pages=n_pages, spec=raw)
            pages.add(n)
    return sorted(pages)


def _check_upper_bound(page: int, *, n_pages: int, spec: str) -> None:
    # Validate before expanding, so a spec like 1-2000000000 is rejected
    # instantly instead of materializing billions of integers into a set.
    if page > n_pages:
        raise RangeParseError(
            f"range {spec!r} references page {page} but document has only {n_pages}"
        )

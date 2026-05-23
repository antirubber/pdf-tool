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
            pages.update(range(lo, hi + 1))
        else:
            pages.add(_parse_int(token, spec=raw))
    result = sorted(pages)
    if result[-1] > n_pages:
        raise RangeParseError(
            f"range {raw!r} references page {result[-1]} but document has only {n_pages}"
        )
    return result

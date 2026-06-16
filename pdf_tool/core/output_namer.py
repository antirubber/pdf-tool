from pathlib import Path
from typing import Callable

_SUFFIX_BY_OPERATION = {
    "encrypt": "encrypted",
    "decrypt": "decrypted",
    "rotate": "rotated",
    "compress": "compressed",
    "ocr": "ocr",
    "watermark": "watermarked",
    "repair": "repaired",
    "merge": "merged",
    "remove": "trimmed",
    "reorder": "reordered",
}

_DIRECTORY_SUFFIX_BY_OPERATION = {
    "split": "pages",
}

_IMAGE_TARGET_FORMATS = frozenset({"png", "jpeg", "jpg", "tiff", "gif"})


def derive_output(input_path: Path, operation: str, **opts: object) -> Path:
    if operation in _SUFFIX_BY_OPERATION:
        suffix = _SUFFIX_BY_OPERATION[operation]
        return input_path.with_stem(f"{input_path.stem}-{suffix}")
    if operation in _DIRECTORY_SUFFIX_BY_OPERATION:
        suffix = _DIRECTORY_SUFFIX_BY_OPERATION[operation]
        return input_path.parent / f"{input_path.stem}-{suffix}"
    if operation == "convert":
        target = opts.get("target_format")
        if not isinstance(target, str):
            raise ValueError("convert requires a string 'target_format' kwarg")
        if target in _IMAGE_TARGET_FORMATS:
            return input_path.parent / f"{input_path.stem}-images"
        return input_path.with_suffix(f".{target}")
    raise ValueError(f"unknown operation {operation!r}")


def ensure_unique(
    candidate: Path,
    exists: Callable[[Path], bool] = Path.exists,
    *,
    as_directory: bool = False,
) -> Path:
    if not exists(candidate):
        return candidate
    n = 2
    while True:
        if as_directory:
            # A directory name may contain dots from the source filename
            # (report.v2-pages); the counter belongs on the whole name, not
            # spliced before a spurious ".v2-pages" "extension".
            next_candidate = candidate.with_name(f"{candidate.name}-{n}")
        else:
            next_candidate = candidate.with_stem(f"{candidate.stem}-{n}")
        if not exists(next_candidate):
            return next_candidate
        n += 1

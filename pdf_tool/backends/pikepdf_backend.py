import functools
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, ParamSpec, TypeVar

import pikepdf

from pdf_tool.core.error_translator import BackendError, PikepdfFailure

_P = ParamSpec("_P")
_R = TypeVar("_R")


def _max_pdf_version(versions: Iterable[str]) -> str:
    """Highest "X.Y" PDF version string, comparing numerically not lexically."""

    def key(v: str) -> tuple[int, int]:
        major, _, minor = v.partition(".")
        try:
            return (int(major), int(minor))
        except ValueError:
            return (0, 0)

    return max(versions, key=key)


def _page_stamp_geometry(
    mediabox: Iterable[object],
) -> tuple[tuple[float, float], tuple[float, float, float, float]]:
    """Return ((width, height), (x0, y0, x1, y1)) from a page's own mediabox.

    Sizing each stamp to the page's box and overlaying at its lower-left
    origin keeps the watermark centred and on-page for mixed-size documents
    and pages whose mediabox origin is not (0, 0).
    """
    x0, y0, x1, y1 = (float(v) for v in mediabox)
    return (x1 - x0, y1 - y0), (x0, y0, x1, y1)


def _translates(method: Callable[_P, _R]) -> Callable[_P, _R]:
    """Convert pikepdf and OS exceptions into a BackendError(PikepdfFailure).

    A single seam at the Backend boundary so every pikepdf Operation surfaces a
    Friendly-path message in default mode and a full traceback only under
    --debug (the original exception is chained via ``from``). BackendError that
    a method raised deliberately passes through untouched.
    """

    @functools.wraps(method)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        try:
            return method(*args, **kwargs)
        except BackendError:
            raise
        except pikepdf.PasswordError as e:
            raise BackendError(PikepdfFailure("PasswordError", str(e))) from e
        except (pikepdf.PdfError, ValueError, OSError) as e:
            raise BackendError(PikepdfFailure(type(e).__name__, str(e))) from e

    return wrapper


@dataclass(frozen=True)
class EncryptOptions:
    password: str
    owner_password: str | None = None
    strength: int = 256  # 256-bit AES / 128-bit AES / 40-bit RC4
    allow_print: bool = True
    allow_copy: bool = True
    allow_modify: bool = True
    allow_annotate: bool = True


# strength -> pikepdf.Encryption params. 40-bit is legacy RC4 and cannot
# encrypt metadata (R < 4), so it disables AES and metadata encryption.
_ENCRYPTION_BY_STRENGTH: dict[int, dict[str, object]] = {
    256: {"R": 6, "aes": True, "metadata": True},
    128: {"R": 4, "aes": True, "metadata": True},
    40: {"R": 2, "aes": False, "metadata": False},
}


@dataclass(frozen=True)
class DecryptOptions:
    password: str


PageNumberStyle = Literal["plain", "of_total", "page_n", "bates"]

_PAGE_NUMBER_POSITIONS: dict[str, tuple[str, str]] = {
    "bottom-center": ("bottom", "center"),
    "bottom-left": ("bottom", "left"),
    "bottom-right": ("bottom", "right"),
    "top-center": ("top", "center"),
    "top-left": ("top", "left"),
    "top-right": ("top", "right"),
}


@dataclass(frozen=True)
class PageNumberOptions:
    pages: list[int]
    start: int = 1
    style: PageNumberStyle = "plain"
    position: str = "bottom-center"
    bates_prefix: str = ""
    bates_width: int = 6
    font_size: int = 12
    margin: float = 36.0


def format_page_label(
    number: int,
    *,
    total: int,
    style: str = "plain",
    bates_prefix: str = "",
    bates_width: int = 6,
) -> str:
    if style == "of_total":
        return f"{number} of {total}"
    if style == "page_n":
        return f"Page {number}"
    if style == "bates":
        return f"{bates_prefix}{number:0{bates_width}d}"
    return str(number)


def _label_xy(
    position: str, width: float, height: float, margin: float, text_width: float
) -> tuple[float, float]:
    vert, horiz = _PAGE_NUMBER_POSITIONS.get(position, ("bottom", "center"))
    y = margin if vert == "bottom" else height - margin
    if horiz == "left":
        x = margin
    elif horiz == "right":
        x = max(margin, width - margin - text_width)
    else:
        x = (width - text_width) / 2
    return x, y


@dataclass(frozen=True)
class WatermarkOptions:
    text: str
    pages: list[int]
    opacity: float = 0.3
    gray: float = 0.5
    font_size: int = 60
    angle_degrees: float = 45.0


_DOCINFO_KEYS: tuple[str, ...] = (
    "/Title",
    "/Author",
    "/Subject",
    "/Keywords",
    "/Creator",
    "/Producer",
    "/CreationDate",
    "/ModDate",
)


@dataclass(frozen=True)
class PdfInfo:
    n_pages: int | None
    encrypted: bool
    metadata: dict[str, str] = field(default_factory=dict)
    file_size: int | None = None
    pdf_version: str | None = None
    page_size: tuple[float, float] | None = None
    page_label: str | None = None
    has_text: bool | None = None


# Standard paper sizes in points (portrait orientation).
_PAPER_SIZES: dict[str, tuple[float, float]] = {
    "A3": (842.0, 1191.0),
    "A4": (595.0, 842.0),
    "A5": (420.0, 595.0),
    "Letter": (612.0, 792.0),
    "Legal": (612.0, 1008.0),
    "Tabloid": (792.0, 1224.0),
}

_TEXT_OPERATORS: tuple[bytes, ...] = (b"Tj", b"TJ")


def _dimension_label(width: float, height: float, tol: float = 3.0) -> str:
    low, high = sorted((width, height))
    orientation = "portrait" if height >= width else "landscape"
    for name, (pw, ph) in _PAPER_SIZES.items():
        if abs(low - pw) <= tol and abs(high - ph) <= tol:
            return f"{name} {orientation}"
    return f"{orientation} ({width:.0f}×{height:.0f} pt)"


def _page_streams(page: "pikepdf.Page") -> Iterable[bytes]:
    obj = page.obj
    contents = obj.get("/Contents")
    if contents is not None:
        if isinstance(contents, pikepdf.Array):
            for stream in contents:
                yield stream.read_bytes()
        else:
            yield contents.read_bytes()
    resources = obj.get("/Resources")
    if resources is None:
        return
    xobjects = resources.get("/XObject")
    if xobjects is None:
        return
    for name in xobjects.keys():
        form = xobjects[name]
        if form.get("/Subtype") == pikepdf.Name("/Form"):
            yield form.read_bytes()


def _has_text_layer(pdf: "pikepdf.Pdf") -> bool:
    for page in pdf.pages:
        for stream in _page_streams(page):
            if any(op in stream for op in _TEXT_OPERATORS):
                return True
    return False


class PikepdfBackend:
    @_translates
    def encrypt(
        self, input_path: Path, output_path: Path, options: EncryptOptions
    ) -> Path:
        from pikepdf import Permissions

        params = _ENCRYPTION_BY_STRENGTH.get(
            options.strength, _ENCRYPTION_BY_STRENGTH[256]
        )
        permissions = Permissions(
            extract=options.allow_copy,
            modify_annotation=options.allow_annotate,
            modify_assembly=options.allow_modify,
            modify_form=options.allow_modify,
            modify_other=options.allow_modify,
            print_lowres=options.allow_print,
            print_highres=options.allow_print,
        )
        with pikepdf.open(input_path) as pdf:
            pdf.save(
                output_path,
                encryption=pikepdf.Encryption(
                    owner=options.owner_password or options.password,
                    user=options.password,
                    allow=permissions,
                    **params,
                ),
            )
        return output_path

    @_translates
    def decrypt(
        self, input_path: Path, output_path: Path, options: DecryptOptions
    ) -> Path:
        with pikepdf.open(input_path, password=options.password) as pdf:
            pdf.save(output_path)
        return output_path

    @_translates
    def rotate(
        self,
        input_path: Path,
        output_path: Path,
        *,
        pages: list[int],
        degrees: int,
    ) -> Path:
        with pikepdf.open(input_path) as pdf:
            for page_num in pages:
                pdf.pages[page_num - 1].rotate(degrees, relative=True)
            pdf.save(output_path)
        return output_path

    @_translates
    def split_every_page(self, input_path: Path, output_dir: Path) -> list[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        outputs: list[Path] = []
        with pikepdf.open(input_path) as src:
            width = len(str(len(src.pages)))
            for i, page in enumerate(src.pages, start=1):
                dst = pikepdf.new()
                dst.pages.append(page)
                out_path = output_dir / f"page-{i:0{width}d}.pdf"
                dst.save(out_path, min_version=src.pdf_version)
                outputs.append(out_path)
        return outputs

    @_translates
    def split_every_n(
        self, input_path: Path, output_dir: Path, *, n: int
    ) -> list[Path]:
        if n < 1:
            raise ValueError(f"split_every_n requires n >= 1 (got {n})")
        output_dir.mkdir(parents=True, exist_ok=True)
        outputs: list[Path] = []
        with pikepdf.open(input_path) as src:
            total = len(src.pages)
            num_chunks = (total + n - 1) // n
            width = len(str(num_chunks))
            for chunk_idx in range(num_chunks):
                start = chunk_idx * n
                end = min(start + n, total)
                dst = pikepdf.new()
                for i in range(start, end):
                    dst.pages.append(src.pages[i])
                out_path = output_dir / f"part-{chunk_idx + 1:0{width}d}.pdf"
                dst.save(out_path, min_version=src.pdf_version)
                outputs.append(out_path)
        return outputs

    @_translates
    def split_at_boundaries(
        self, input_path: Path, output_dir: Path, *, boundaries: list[int]
    ) -> list[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        outputs: list[Path] = []
        with pikepdf.open(input_path) as src:
            total = len(src.pages)
            sorted_bounds = sorted(b for b in boundaries if 1 < b <= total)
            cut_points = [1, *sorted_bounds, total + 1]
            num_chunks = len(cut_points) - 1
            width = len(str(num_chunks))
            for idx in range(num_chunks):
                start = cut_points[idx]
                end = cut_points[idx + 1]
                if start >= end:
                    continue
                dst = pikepdf.new()
                for page_num in range(start, end):
                    dst.pages.append(src.pages[page_num - 1])
                out_path = output_dir / f"part-{idx + 1:0{width}d}.pdf"
                dst.save(out_path, min_version=src.pdf_version)
                outputs.append(out_path)
        return outputs

    @_translates
    def extract_pages(
        self, input_path: Path, output_path: Path, *, pages: list[int]
    ) -> Path:
        with pikepdf.open(input_path) as src:
            dst = pikepdf.new()
            for page_num in pages:
                dst.pages.append(src.pages[page_num - 1])
            dst.save(output_path, min_version=src.pdf_version)
        return output_path

    @_translates
    def reorder_pages(
        self, input_path: Path, output_path: Path, *, order: list[int]
    ) -> Path:
        with pikepdf.open(input_path) as src:
            dst = pikepdf.new()
            for page_num in order:
                dst.pages.append(src.pages[page_num - 1])
            dst.save(output_path, min_version=src.pdf_version)
        return output_path

    @_translates
    def remove_pages(
        self, input_path: Path, output_path: Path, *, pages: list[int]
    ) -> Path:
        remove = set(pages)
        with pikepdf.open(input_path) as src:
            keep = [
                i for i in range(1, len(src.pages) + 1) if i not in remove
            ]
            if not keep:
                raise ValueError("removing every page would leave an empty PDF")
            dst = pikepdf.new()
            for page_num in keep:
                dst.pages.append(src.pages[page_num - 1])
            dst.save(output_path, min_version=src.pdf_version)
        return output_path

    @_translates
    def watermark(
        self, input_path: Path, output_path: Path, options: WatermarkOptions
    ) -> Path:
        from pikepdf import Matrix, Name, Page, Rectangle
        from pikepdf.canvas import Canvas, Color, Helvetica, Text

        target_pages = set(options.pages)
        with pikepdf.open(input_path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                if i not in target_pages:
                    continue
                (width, height), rect = _page_stamp_geometry(page.mediabox)

                canvas = Canvas(page_size=(width, height))
                canvas.add_font(Name("/PdfToolHelv"), Helvetica())
                with canvas.do.save_state():
                    canvas.do.fill_color(
                        Color(
                            options.gray, options.gray, options.gray, options.opacity
                        )
                    )
                    transform = (
                        Matrix.identity()
                        .rotated(options.angle_degrees)
                        .translated(width / 2, height / 2)
                    )
                    canvas.do.cm(transform)
                    text = Text()
                    text.font("/PdfToolHelv", options.font_size)
                    # Rough horizontal centring: char width ≈ 0.5 * font_size
                    text.text_transform(
                        Matrix.identity().translated(
                            -0.25 * options.font_size * len(options.text), 0.0
                        )
                    )
                    text.show(options.text)
                    canvas.do.draw_text(text)
                stamp_pdf = canvas.to_pdf()
                Page(page).add_overlay(Page(stamp_pdf.pages[0]), Rectangle(*rect))
            pdf.save(output_path)
        return output_path

    @_translates
    def add_page_numbers(
        self, input_path: Path, output_path: Path, options: PageNumberOptions
    ) -> Path:
        from pikepdf import Matrix, Name, Page, Rectangle
        from pikepdf.canvas import Canvas, Color, Helvetica, Text

        target = set(options.pages)
        with pikepdf.open(input_path) as pdf:
            total = len(pdf.pages)
            stamped = 0
            for i, page in enumerate(pdf.pages, start=1):
                if i not in target:
                    continue
                label = format_page_label(
                    options.start + stamped,
                    total=total,
                    style=options.style,
                    bates_prefix=options.bates_prefix,
                    bates_width=options.bates_width,
                )
                stamped += 1
                (width, height), rect = _page_stamp_geometry(page.mediabox)
                text_width = 0.5 * options.font_size * len(label)
                x, y = _label_xy(
                    options.position, width, height, options.margin, text_width
                )
                canvas = Canvas(page_size=(width, height))
                canvas.add_font(Name("/PdfToolHelv"), Helvetica())
                with canvas.do.save_state():
                    canvas.do.fill_color(Color(0.0, 0.0, 0.0, 1.0))
                    text = Text()
                    text.font("/PdfToolHelv", options.font_size)
                    text.text_transform(Matrix.identity().translated(x, y))
                    text.show(label)
                    canvas.do.draw_text(text)
                stamp_pdf = canvas.to_pdf()
                Page(page).add_overlay(Page(stamp_pdf.pages[0]), Rectangle(*rect))
            pdf.save(output_path, min_version=pdf.pdf_version)
        return output_path

    @_translates
    def set_metadata(
        self, input_path: Path, output_path: Path, *, fields: dict[str, str]
    ) -> Path:
        with pikepdf.open(input_path) as pdf:
            for name, value in fields.items():
                key = name if name.startswith("/") else f"/{name}"
                if value == "":
                    if key in pdf.docinfo:
                        del pdf.docinfo[key]
                else:
                    pdf.docinfo[key] = value
            pdf.save(output_path)
        return output_path

    @_translates
    def strip_metadata(self, input_path: Path, output_path: Path) -> Path:
        with pikepdf.open(input_path) as pdf:
            for key in list(pdf.docinfo.keys()):
                del pdf.docinfo[key]
            if "/Info" in pdf.trailer:
                del pdf.trailer["/Info"]
            if "/ID" in pdf.trailer:
                del pdf.trailer["/ID"]
            if "/Metadata" in pdf.Root:
                del pdf.Root["/Metadata"]
            # qpdf reuses the cached original /ID across a plain save even if
            # the trailer key is removed; deleting it AND requesting a
            # deterministic (content-derived) id drops the original fingerprint.
            pdf.save(output_path, deterministic_id=True)
        return output_path

    @_translates
    def try_repair(self, input_path: Path, output_path: Path) -> Path:
        with pikepdf.open(input_path, attempt_recovery=True) as pdf:
            pdf.save(output_path)
        return output_path

    @_translates
    def merge(self, input_paths: list[Path], output_path: Path) -> Path:
        dst = pikepdf.new()
        opened: list = []
        try:
            for path in input_paths:
                src = pikepdf.open(path)
                opened.append(src)
                for page in src.pages:
                    dst.pages.append(page)
            dst.save(
                output_path,
                min_version=_max_pdf_version(s.pdf_version for s in opened),
            )
        finally:
            for src in opened:
                src.close()
        return output_path

    @_translates
    def inspect(self, input_path: Path) -> "PdfInfo":
        file_size = input_path.stat().st_size
        try:
            pdf = pikepdf.open(input_path)
        except pikepdf.PasswordError:
            return PdfInfo(n_pages=None, encrypted=True, file_size=file_size)
        with pdf:
            metadata = {}
            try:
                docinfo = pdf.docinfo
            except Exception:
                docinfo = None
            if docinfo is not None:
                for key in _DOCINFO_KEYS:
                    if key in docinfo:
                        metadata[key.lstrip("/")] = str(docinfo[key])
            page_size = None
            page_label = None
            if pdf.pages:
                box = pdf.pages[0].mediabox
                width = float(box[2]) - float(box[0])
                height = float(box[3]) - float(box[1])
                page_size = (width, height)
                page_label = _dimension_label(width, height)
            return PdfInfo(
                n_pages=len(pdf.pages),
                encrypted=pdf.is_encrypted,
                metadata=metadata,
                file_size=file_size,
                pdf_version=pdf.pdf_version,
                page_size=page_size,
                page_label=page_label,
                has_text=_has_text_layer(pdf),
            )

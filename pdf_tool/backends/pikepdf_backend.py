import functools
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import ParamSpec, TypeVar

import pikepdf

from pdf_tool.core.error_translator import BackendError, PikepdfFailure

_P = ParamSpec("_P")
_R = TypeVar("_R")


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


@dataclass(frozen=True)
class DecryptOptions:
    password: str


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


class PikepdfBackend:
    @_translates
    def encrypt(
        self, input_path: Path, output_path: Path, options: EncryptOptions
    ) -> Path:
        with pikepdf.open(input_path) as pdf:
            pdf.save(
                output_path,
                encryption=pikepdf.Encryption(
                    owner=options.owner_password or options.password,
                    user=options.password,
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
                dst.save(out_path)
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
                dst.save(out_path)
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
                dst.save(out_path)
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
            dst.save(output_path)
        return output_path

    @_translates
    def watermark(
        self, input_path: Path, output_path: Path, options: WatermarkOptions
    ) -> Path:
        from pikepdf import Matrix, Name, Page, Rectangle
        from pikepdf.canvas import Canvas, Color, Helvetica, Text

        with pikepdf.open(input_path) as pdf:
            page_size = (612.0, 792.0)
            if pdf.pages:
                box = pdf.pages[0].mediabox
                page_size = (float(box[2] - box[0]), float(box[3] - box[1]))

            canvas = Canvas(page_size=page_size)
            canvas.add_font(Name("/PdfToolHelv"), Helvetica())
            with canvas.do.save_state():
                canvas.do.fill_color(
                    Color(options.gray, options.gray, options.gray, options.opacity)
                )
                cx, cy = page_size[0] / 2, page_size[1] / 2
                transform = (
                    Matrix.identity()
                    .rotated(options.angle_degrees)
                    .translated(cx, cy)
                )
                canvas.do.cm(transform)
                text = Text()
                text.font("/PdfToolHelv", options.font_size)
                # Rough horizontal centring: estimate char width ≈ 0.5 * font_size
                text.text_transform(
                    Matrix.identity().translated(
                        -0.25 * options.font_size * len(options.text), 0.0
                    )
                )
                text.show(options.text)
                canvas.do.draw_text(text)
            stamp_pdf = canvas.to_pdf()

            target_pages = set(options.pages)
            stamp_page = Page(stamp_pdf.pages[0])
            rect = Rectangle(0, 0, page_size[0], page_size[1])
            for i, page in enumerate(pdf.pages, start=1):
                if i in target_pages:
                    Page(page).add_overlay(stamp_page, rect)
            pdf.save(output_path)
        return output_path

    @_translates
    def set_metadata(
        self, input_path: Path, output_path: Path, *, fields: dict[str, str]
    ) -> Path:
        with pikepdf.open(input_path) as pdf:
            for name, value in fields.items():
                key = name if name.startswith("/") else f"/{name}"
                pdf.docinfo[key] = value
            pdf.save(output_path)
        return output_path

    @_translates
    def strip_metadata(self, input_path: Path, output_path: Path) -> Path:
        with pikepdf.open(input_path) as pdf:
            for key in list(pdf.docinfo.keys()):
                del pdf.docinfo[key]
            with pdf.open_metadata() as xmp:
                for key in list(xmp.keys()):
                    del xmp[key]
            pdf.save(output_path)
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
            dst.save(output_path)
        finally:
            for src in opened:
                src.close()
        return output_path

    @_translates
    def inspect(self, input_path: Path) -> "PdfInfo":
        try:
            pdf = pikepdf.open(input_path)
        except pikepdf.PasswordError:
            return PdfInfo(n_pages=None, encrypted=True)
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
            return PdfInfo(
                n_pages=len(pdf.pages),
                encrypted=pdf.is_encrypted,
                metadata=metadata,
            )

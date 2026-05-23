# Wrapper architecture with `pikepdf` as primary backend

## Status

Accepted.

## Decision

PDF Tool is structured as a thin wizard UI over a set of **Backends** that do the actual work. `pikepdf` is the primary Backend and is used wherever it can do the job natively; a small set of external CLI binaries (`libreoffice`, `ghostscript`, `ocrmypdf`, `pdftoppm`/`pdftotext`, `img2pdf`) are secondary Backends invoked via `subprocess` only for the Operations `pikepdf` cannot handle.

Concretely, the Operation → Backend mapping is:

| Operation | Primary Backend | Why |
|---|---|---|
| Encrypt / Decrypt | `pikepdf` | Native AES-40/128/256, permission flags, no shell-out |
| Split (all modes) | `pikepdf` | Native page extraction, fast, atomic |
| Merge | `pikepdf` | Native, preserves metadata |
| Rotate | `pikepdf` | Native page rotation |
| Inspect | `pikepdf` | Native metadata, page count, encryption status |
| Watermark | `pikepdf` | Native PDF stamping |
| Metadata edit | `pikepdf` | Native XMP/Info dict manipulation |
| Repair | `pikepdf` (fallback `ghostscript`) | `pikepdf` opens many malformed PDFs; `gs` is the last resort |
| Compress | `ghostscript` | No native Python equivalent for real recompression |
| Convert: Office ↔ PDF | `libreoffice --headless` | No Python-native renderer for Office formats |
| Convert: PDF → image | `pdftoppm` (poppler-utils) | `pikepdf` doesn't rasterize; `mutool` was the original choice but poppler is more widely available |
| Convert: image → PDF | `img2pdf` | Lossless image embedding; Pillow+pikepdf is a fallback |
| Convert: PDF → text | `pdftotext` (poppler-utils) | `pikepdf` doesn't extract text layout; `mutool` was the original choice but poppler is more widely available |
| OCR | `ocrmypdf` | Orchestrates tesseract + ghostscript correctly |

## Considered Options

### Pure shell-out (rejected)

Drive everything via `subprocess`, mostly through `qpdf` and `libreoffice`. Originally the obvious shape — three named tools, no Python PDF lib.

Rejected because:

- `pikepdf` wraps `libqpdf` (the same C++ engine `qpdf` exposes on the command line). Shelling out to `qpdf` from Python when `pikepdf` exposes the same engine in-process is gratuitous — slower, harder to error-handle, no streaming, no random access to the PDF object model.
- `pdftk` is essentially unmaintained and a pain to install on modern macOS (the `pdftk-java` workaround needs a JRE).
- Per-op subprocess work multiplies: argv construction, stderr parsing, exit-code interpretation, temp-file management, signal handling. `pikepdf` collapses 7+ of the 11 Operations into native Python calls with proper exceptions.

### Pure native Python (rejected)

Use only Python libraries (`pikepdf`, `pypdf`, `Pillow`, `pdfminer.six`, `python-pptx`, etc.) — no external binaries at all.

Rejected because:

- **Office ↔ PDF has no Python-native equivalent.** Every serious solution shells out to LibreOffice or Microsoft Word under the hood. There is no path to dropping that dep without dropping the feature.
- **OCR needs tesseract.** `ocrmypdf` is the canonical orchestrator; reimplementing its preprocessing/postprocessing in Python is a large project on its own.
- **PDF rasterization** (`PDF → image`) needs a renderer — `mupdf` (via `mutool`) or `poppler` (via `pdftoppm`). Python wrappers exist (`PyMuPDF`) but are GPL-encumbered (`PyMuPDF` is AGPL unless commercial-licensed), which constrains downstream distribution.

### `pypdf` instead of `pikepdf` (rejected)

Use the pure-Python `pypdf` package as the primary Backend.

Rejected because:

- `pypdf` does not implement AES-256 encryption robustly, and historically has had correctness issues with permission flags and password handling. For a tool whose marquee non-Convert feature is encryption, this is disqualifying.
- `pypdf` is meaningfully slower than `pikepdf` on large PDFs because it's pure Python; `libqpdf` is C++.
- `pypdf` handles malformed PDFs less gracefully than `libqpdf`, which has decades of edge-case handling.

The tradeoff `pypdf` offers — pure Python, no C extension — is real but doesn't matter for our distribution model (Homebrew formula and `pipx` both handle wheels with C extensions transparently on the platforms we support).

### `pdfcpu` as the encryption/page-ops Backend (rejected)

`pdfcpu` is a strong, actively-maintained Go-based PDF toolkit with a single-binary distribution.

Rejected because:

- No Python bindings — using it means shelling out, which lands us back at the per-op subprocess cost we rejected for `qpdf`.
- Adds a runtime binary dep for capabilities `pikepdf` already provides in-process. Worth revisiting only if a specific Operation surfaces that `pikepdf` cannot handle and `pdfcpu` can.

## Consequences

- **Mixed error surface.** Native Backend errors arrive as Python exceptions (`pikepdf.PdfError`, `pikepdf.PasswordError`, etc.); shell-out Backend errors arrive as non-zero exit codes plus stderr text. The Friendly path error-translation table (see Q13) needs to handle both shapes uniformly. Each shell-out Backend gets its own small set of recognised-error mappings.
- **Heterogeneous availability.** `pikepdf` is a pip dependency and is therefore always present after install. The shell-out Backends are *system* dependencies and may be missing — handled by the startup probe and degraded menu (Q8). This means the menu visibly changes depending on what's installed, which is good UX but needs to be documented for new contributors who'll wonder why an Operation "disappeared".
- **Wheel size.** `pikepdf` carries a `libqpdf` C extension (~5–10MB per wheel). Acceptable on the platforms we target (macOS + Linux).
- **Test isolation.** Native Backend tests run in-process and are fast. Shell-out Backend tests require the actual binaries on the test runner — CI needs `libreoffice`, `ghostscript`, `ocrmypdf` installed, or those tests need to be skipped/mocked. Plan: integration tests that exercise real binaries gated behind a `--integration` flag; unit tests stub the subprocess layer.
- **Upgrade path for adding a new Operation.** First ask: can `pikepdf` do it? If yes, the Operation is ~50 lines and needs no new system dep. If no, identify the minimal external binary, add it to the startup probe, document it in the Homebrew formula, write a subprocess adapter with its own error translations.
- **Lock-in to libqpdf.** Effectively all non-Convert Operations are coupled to the libqpdf object model. If `libqpdf` ever stagnates or breaks compat, we'd have to migrate a lot of code at once. Mitigated by `libqpdf`'s long track record and active maintenance; flagged here so it's a known concentration of risk.

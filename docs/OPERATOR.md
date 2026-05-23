# Operator Guide

This guide is for whoever picks up the codebase next — either to continue building, debug a failure, or ship a release. It assumes you have already read `CONTEXT.md` (the glossary) and `docs/PRD.md` (the spec).

## Current state

End-to-end runnable. `pdf-tool` launches the wizard, the menu shows all 11 Operations (disabled with install hints where their Backend is missing), and the full happy path works for every Operation backed by a locally-available Backend. **96 tests pass.**

What is done:

| Layer | Modules |
|---|---|
| Pure-core | `range_parser`, `output_namer`, `page_selection`, `probe`, `error_translator` |
| Backends | `pikepdf_backend` (encrypt, decrypt, inspect, rotate, split×4, merge, set/strip metadata, watermark, try_repair), `subprocess_backend` (base class), `ghostscript_backend` (compress), `libreoffice_backend` (convert), `poppler_backend` (pdf→img, pdf→text), `img2pdf_backend` (img→pdf), `ocrmypdf_backend` (add_text_layer) |
| Operations | `encrypt`, `decrypt`, `inspect`, `rotate`, `split`, `merge`, `metadata`, `watermark`, `repair`, `compress`, `convert`, `ocr` |
| Widgets | `file_input`, `page_selection`, `batch` |
| UI | `wizard` (menu + dispatch with degraded-Backend gating), `cli` (typer, `--version` / `--debug`) |

Batch mode is wired for **Encrypt** and **Compress** (the two Operations where it's most useful per PRD user story 16); extending to other Operations follows the same `prompt_one_or_many` → `collect_input_files` → `run_per_file` pattern in `widgets/batch.py`.

## Known gaps / deferred work

In rough priority order:

1. **Repair → ghostscript fallback.** `PikepdfBackend.try_repair` works; the gs fallback declared in ADR-0001 is not yet wired. Add it once a real corrupt-PDF case shows pikepdf alone isn't enough — premature otherwise.
2. **Batch mode for the other 10 Operations.** The helper is reusable: refactor each handler's `run()` into `_run_one()` + `_run_batch()` exactly the way `operations/encrypt.py` and `operations/compress.py` do it.
3. **Error translator coverage.** The table currently knows pikepdf `PasswordError` and falls back to a generic message. Add a row per known Backend failure mode as you encounter them — ghostscript exit codes, libreoffice "no export filter", ocrmypdf `ExitCode.already_done_ocr` (6), etc. The `SubprocessFailure` shape (binary, exit_code, stderr) is already there to match on.
4. **Advanced options for Encrypt** — encryption strength (40/128/256) and per-permission flags (print/copy/modify/annotate). PRD user story 29; `pikepdf.Encryption(R=…, allow=Permissions(…))` is the API. Today we default to R=6 (AES-256) with default `Permissions(modify_assembly=False, everything-else=True)`.
5. **Advanced options for Compress** — DPI and JPEG quality knobs. PRD user story 45.
6. **PDF → image / PDF → text** now use `pdftoppm` / `pdftotext` from poppler-utils (replacing the speculative `mutool` backend). Integration tests are `@pytest.mark.skipif` gated on those binaries being present.
7. **Drag-and-drop polish.** `widgets/file_input.normalize_path` strips surrounding quotes and expands `~` (verified by 5 unit tests). Some terminals paste with extra escape characters; revisit if a real user reports breakage.

## Environment

`uv` is the env manager. Python `>= 3.12` (pinned in `pyproject.toml`).

```bash
uv sync --dev                            # create venv, install runtime + dev deps
uv run pdf-tool                          # launch the wizard
uv run pdf-tool --version                # 0.0.1
uv run pdf-tool --debug                  # PDF_TOOL_DEBUG=1 also works
```

### Installing as a global binary

`pdf-tool` can be installed as a CLI tool available from anywhere, instead of requiring `uv run` from the project directory:

```bash
uv tool install .                       # install, symlinks `pdf-tool` onto PATH
pdf-tool                                # works from any directory
uv tool install --force .               # reinstall after code changes
uv tool uninstall pdf-tool              # remove later
```

For an editable install (code changes reflected immediately without reinstalling):

```bash
pipx install -e .
```

The `[project.scripts]` entry point in `pyproject.toml` (`pdf-tool = "pdf_tool.cli:app"`) makes this work.

uv run pytest                            # all 96 tests
uv run pytest -m integration             # only tests that touch real binaries
uv run pytest -m "not integration"       # only pure-Python tests
uv run pytest -k "encrypt"               # filter by keyword
uv run pytest tests/backends/ -v         # one module, verbose
```

The `integration` marker is declared in `pyproject.toml`. Today's integration tests cover ghostscript and libreoffice; they `skipif` the binary is missing, so CI doesn't break when a runner lacks them.

## System dependencies

| Backend | Binary probed | Install (macOS / Linuxbrew) |
|---|---|---|
| `LibreOfficeBackend` | `libreoffice` or `soffice` | `brew install libreoffice` |
| `GhostscriptBackend` | `gs` | `brew install ghostscript` |
| `OcrmypdfBackend` | `ocrmypdf` (pulls in tesseract) | `brew install ocrmypdf` |
| `PdftoppmBackend` | `pdftoppm` | `brew install poppler` |
| `PdftotextBackend` | `pdftotext` | `brew install poppler` |
| `Img2pdfBackend` | `img2pdf` | `brew install img2pdf` |

Quick probe:

```bash
uv run python -c "from pdf_tool.core.probe import probe; from pprint import pprint; pprint(probe())"
```

The startup probe also drives the wizard menu: Operations whose required Backends are all missing appear greyed-out with the install hint inline (e.g. `OCR (install: brew install ocrmypdf)`). Convert is enabled if **any** of `libreoffice` / `pdftoppm` / `pdftotext` / `img2pdf` is present and self-degrades inside the handler based on which direction the user picks.

## Project layout

```
pdf-tool/
├── CONTEXT.md                                       glossary — read first
├── pyproject.toml                                   package + deps + pytest config
├── pdf_tool/
│   ├── __init__.py                                  __version__
│   ├── cli.py                                       typer entry: --version, --debug
│   ├── wizard.py                                    top-level: probe → menu → handler
│   ├── core/                                        deep, pure modules — testable spine
│   │   ├── range_parser.py
│   │   ├── output_namer.py
│   │   ├── page_selection.py
│   │   ├── probe.py
│   │   └── error_translator.py                      PikepdfFailure / SubprocessFailure / FriendlyError / translate
│   ├── backends/
│   │   ├── pikepdf_backend.py                       all in-process pikepdf calls funnel here
│   │   ├── subprocess_backend.py                    base class: argv, stderr, exit code, timeout
│   │   ├── ghostscript_backend.py                   compress
│   │   ├── libreoffice_backend.py                   convert via --headless --convert-to
│   │   ├── poppler_backend.py                     pdf_to_images, pdf_to_text
│   │   ├── img2pdf_backend.py                       images_to_pdf
│   │   └── ocrmypdf_backend.py                      add_text_layer
│   ├── operations/                                  one module per Operation
│   │   ├── encrypt.py     decrypt.py     inspect.py
│   │   ├── rotate.py      split.py       merge.py
│   │   ├── metadata.py    watermark.py   repair.py
│   │   └── compress.py    convert.py     ocr.py
│   └── widgets/
│       ├── file_input.py                            prompt + normalize_path (strips drag-and-drop quotes, expands ~)
│       ├── page_selection.py                        the shared Page Selection prompt
│       └── batch.py                                 prompt_one_or_many, collect_input_files, run_per_file, print_summary
├── tests/
│   ├── conftest.py                                  make_pdf / sample_pdf fixtures (build PDFs in-process via pikepdf)
│   ├── core/                                        unit tests, mirroring pdf_tool/core/
│   ├── backends/                                    backend tests (pikepdf + subprocess + ghostscript + libreoffice)
│   ├── widgets/                                     normalize_path tests
│   └── fixtures/                                    (empty — fixtures are built in-process by conftest)
└── docs/
    ├── PRD.md                                       full spec
    ├── OPERATOR.md                                  this file
    └── adr/
        └── 0001-wrapper-architecture-pikepdf-primary.md
```

## How development is being done

Test-driven, vertical slices. **Do not** write all tests for a module and then write the implementation — that produces tests of imagined behaviour, not actual behaviour. For each behaviour:

1. Add one failing test that names the behaviour.
2. Run `uv run pytest <test-file>` and confirm RED.
3. Write the minimum implementation to pass.
4. Run again and confirm GREEN.
5. Repeat.

If a new test passes without any implementation change, **keep it anyway** — it's now a regression guard.

Only refactor while GREEN. If you find yourself wanting to clean up while RED, get to GREEN first.

## How to add a new Operation

The shape of every Operation is the same; adding one is mechanical:

1. **Pick the Backend.** Check the Operation → Backend table in `docs/adr/0001-…md`. If pikepdf can do it natively, add a method to `PikepdfBackend`. If not, use an existing `SubprocessBackend` subclass or create a new one.
2. **Extend the output namer.** Add an entry in `_SUFFIX_BY_OPERATION` or `_DIRECTORY_SUFFIX_BY_OPERATION` in `core/output_namer.py`. Add a parametrised test row.
3. **TDD the Backend method.** RED-GREEN for the happy path; RED-GREEN for each known failure mode (every named failure becomes a row in the Error translator's table).
4. **Write the Operation handler in `operations/<op>.py`.** It owns the prompt sequence: file input → essentials → optional `Advanced options?` gate → confirm Auto-derived output → invoke Backend → render result. Keep it as plumbing — no logic.
5. **Register it in the wizard.** Add a `_MenuEntry` to `_OPERATIONS` in `wizard.py` with the required Backend(s). It auto-degrades when any required Backend is `Missing`.

The four pure-core modules exist precisely so Step 4 stays small.

## How to add Batch mode to an Operation

Pattern lifted from `operations/encrypt.py`:

1. Extract the handler's existing logic into `_run_one()`.
2. Write `_run_batch()`: call `collect_input_files()` for the inputs, prompt for any shared options (one password, one preset, etc.), define a local `process(path) -> Path` closure, then call `run_per_file(operation_name, inputs, process)` and `print_summary(outcomes)`.
3. Rewrite `run()` as: `mode = prompt_one_or_many(); if mode == "one": _run_one(); elif mode == "many": _run_batch()`.

Batch makes sense for any Operation where the user has many similar files and would otherwise relaunch the wizard per file. Skip it for Operations that are intrinsically one-shot (Merge — input is already a set of files; Inspect — output is screen text).

## How to extend the Error translator

`core/error_translator.translate(operation, failure) -> FriendlyError`. The failure is a `BackendFailure` (`PikepdfFailure` or `SubprocessFailure`); the message is what the user sees on the Friendly path.

To teach it a new mapping:

1. Run the Operation that produces the bad case once, capture the actual exception/stderr. The Backend wrapper raises `BackendError(failure)`; pull the failure shape from `e.failure`.
2. Add a `case` branch to `translate` that matches that shape and returns a `FriendlyError` with a plain-English message and (optionally) a `suggested_action`.
3. Add a test in `tests/core/test_error_translator.py` (table-driven preferred; one row per case).

Known mappings worth adding next:

- `SubprocessFailure(binary="ocrmypdf", exit_code=6, …)` → `"This PDF already has a text layer. Use Advanced options → Force re-OCR if you want to redo it."`
- `SubprocessFailure(binary="ocrmypdf", exit_code=8, …)` → `"This PDF is password-protected. Use Decrypt first."`
- `SubprocessFailure(binary="libreoffice", stderr=~"no export filter", …)` → `"LibreOffice cannot convert this file format. Check the file is what you think it is."`
- `SubprocessFailure(binary="gs", exit_code=1, stderr=~"invalid xref", …)` → `"This PDF appears corrupt. Try Repair first."`

## How to read a failing test

- **Range parser** raises `RangeParseError` with a structured message naming the bad token and the original spec.
- **Output namer** raises `ValueError` for unknown Operations and for `convert` without `target_format`. No other raise paths.
- **Page Selection** raises `ValueError` for `FirstN(n)` / `LastN(n)` with `n < 1`. `n_pages = 0` returns `[]` cleanly.
- **Backend probe** never raises; it always returns a complete `BackendAvailability` map covering every `BackendName`.
- **PikepdfBackend** wraps `pikepdf.PasswordError` as `BackendError(PikepdfFailure(exception_name="PasswordError", message=...))`. Other pikepdf exceptions surface unchanged today — wrap them as you find them.
- **SubprocessBackend** raises `BackendError(SubprocessFailure(binary, exit_code, stderr))` on non-zero exit. On timeout, exit_code is `-1` and stderr is `"timed out after Ns"`.

If any of these invariants is violated, something deeper is wrong than the test message suggests — start by re-reading `CONTEXT.md` to make sure terminology hasn't drifted.

## Backend gotchas learned the hard way

- **`pikepdf.PasswordError`** is exported from the package root, but its actual module path is `pikepdf._core.PasswordError`. Import it as `pikepdf.PasswordError`.
- **`pikepdf.Encryption(R=6, aes=True)`** is the default and corresponds to AES-256. Lower R values (4 = AES-128, 2/3 = RC4) are available but inferior; only override under Advanced options.
- **`pikepdf.open(path)`** raises `PasswordError` on an encrypted PDF with no password — it does not return a partially-readable handle. `PikepdfBackend.inspect` catches this and returns `PdfInfo(n_pages=None, encrypted=True)` so Inspect can describe an encrypted file without the password.
- **`pikepdf.canvas.Canvas`** (used by Watermark) requires `Name("/Helv")` for `add_font` (the leading `/` is mandatory); `Color` requires four arguments including alpha; `do.cm(Matrix)` is the only transform API (no high-level `translate`/`rotate` on the accessor — chain on `Matrix.identity().rotated(a).translated(x, y)` instead).
- **LibreOffice exit code 0 does not mean success.** It will happily print `Error: no export filter` on stderr and exit 0 if asked to convert PDF → ODT on a blank/structureless PDF. The integration test uses TXT → PDF (the common direction) for that reason. If a future Operation depends on PDF → DOCX, check stderr too, not just exit code.
- **LibreOffice writes the output to `--outdir/<input_stem>.<ext>`**, not to a user-chosen filename. `LibreOfficeBackend.convert` renames the produced file to the requested `output_path` after the conversion.
- **`pytest --timeout=…`** is not installed; just rely on the per-Backend `timeout=` argument to `_run` / `_check` (default 300s; 180s for LibreOffice; 600s for OCR).
- **`pikepdf.open` defaults to `attempt_recovery=True`** — that's why Repair's happy path is "just open and save". Explicit is still better; `PikepdfBackend.try_repair` passes it for documentation value.

## What lives where, conceptually

- **The glossary** is `CONTEXT.md`. New vocabulary lands there first. Don't let new code use words the glossary doesn't sanction.
- **The architectural decisions** live in `docs/adr/`. Before reopening "why pikepdf? why no Windows? why no scripted mode?" — read the ADRs. They list the alternatives that were considered and rejected, with reasons.
- **The spec** is `docs/PRD.md`. The *Implementation Decisions* and *Out of Scope* sections are the most actionable parts.

## Things to **not** do

- Do **not** import `pikepdf` outside `pdf_tool/backends/pikepdf_backend.py`. All pikepdf calls funnel through that class. (Tests are the only exception — they may open the resulting PDFs directly to assert on properties.)
- Do **not** call `subprocess.run` outside `pdf_tool/backends/`. All shell-outs funnel through a `SubprocessBackend` subclass.
- Do **not** write persistent state to disk. No `~/.pdf-tool/`, no logs, no recent-files cache. Deliberate non-goal (PRD Out of Scope, user story 59).
- Do **not** add subcommands to the CLI. The contract is "launch, prompt, exit". `--debug` / `--version` / `--help` are the only flags. (PRD Out of Scope.)
- Do **not** branch on `os.name == "nt"`. Windows is explicitly out of scope.
- Do **not** write tests that patch private functions, reach into internals, or assert on `print` output. Test the contract through the public interface.
- Do **not** confirm `--version` is `0.0.1` literally in a test — `pdf_tool.__version__` is the single source.

## Sanity checks before committing

```bash
uv run pytest                           # 96 tests, all pass
uv run pdf-tool --version               # 0.0.1
uv run pdf-tool --help                  # renders cleanly, only 3 options
uv run python -c "from pdf_tool import wizard; print('imports OK')"
```

## End-to-end smoke test

A throwaway PTY-driven smoke script lives at `/tmp/smoke_encrypt.py` (recreate it from this file's git history if you blew away `/tmp`). It launches `pdf-tool` in a pseudo-terminal, walks the wizard menu → Encrypt → Just one → password prompts → confirm → asserts the output is openable with the password and not without. Useful when you've made wizard-layer changes and want one cheap end-to-end check before pushing.

It is **not** a CI test (it shells out to a real terminal and `uv run pdf-tool`). Treat it as a manual smoke probe. If you decide to keep one in-tree, drop it under `tests/smoke/` with a clear "manual only" docstring; do not mark it with the `integration` marker (which is for binary-dependent unit-style tests).

---

That's the operating state. The build-up is intentionally narrow — each new slice earns its place by passing tests before any wiring is added.

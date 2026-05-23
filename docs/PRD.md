# PDF Tool — Initial Implementation PRD

## Problem Statement

I have everyday PDF tasks — encrypting a contract, splitting a scanned booklet, converting a `.docx` to PDF or vice versa, compressing a 40MB scan before emailing it — and each task currently requires remembering the right flags for a different CLI tool. `qpdf` has one syntax for encryption, `libreoffice --headless` has another for conversion, `ghostscript` has yet another for compression, and `pdftk` (the one I would have reached for a few years ago) is essentially unmaintained. For me, this is friction. For the terminal-curious non-technical people I want to share the tool with (paralegals, accountants, designers — people who can open a terminal and follow prompts but won't memorise flags or write shell scripts), it's a complete blocker. There is no single, friendly interactive entry point that covers the common PDF needs on macOS and Linux.

## Solution

A single command, `pdf-tool`, that launches a one-shot interactive Wizard. The user picks one Operation from a menu, answers a few prompts (with sensible defaults and an optional "Advanced options" gate for power users), confirms the Auto-derived output path, and the tool runs. Pikepdf does most of the work in-process; libreoffice, ghostscript, ocrmypdf, poppler (pdftoppm, pdftotext), and img2pdf are invoked via subprocess only where pikepdf cannot cover the Operation. On startup the tool probes which Backends are available and degrades the menu accordingly with inline install hints, so a missing dependency surfaces as a helpful note rather than a cryptic crash four prompts deep. Errors are translated into plain-English messages by default, with `--debug` reserved for raw Backend output. The tool is distributed via PyPI for developers (`pipx install pdf-tool`) and a Homebrew tap for non-technical users (one `brew install` pulls in all system dependencies).

## User Stories

**Launch and discovery**

1. As a non-technical user, I want to type `pdf-tool` and see a menu of all operations I can perform, so that I do not need to remember any command syntax.
2. As a non-technical user, I want operations whose backends are missing to be visibly disabled with an install hint, so that I know exactly what to install to unlock them rather than discovering it via a crash.
3. As a power user, I want the tool to start in under one second, so that launching it from terminal feels as cheap as running `ls`.
4. As any user, I want to exit the Wizard at any point with Ctrl+C, so that I am never trapped inside a prompt chain.
5. As a power user, I want a `--version` flag, so that I can confirm which release I have installed.
6. As a power user, I want a `--debug` flag (and a `PDF_TOOL_DEBUG=1` environment variable) that reveals raw Backend output and full tracebacks, so that I can diagnose failures myself.

**File input**

7. As a non-technical user, I want to drag a PDF from Finder into the terminal window to fill in the input path prompt, so that I do not need to know what an absolute path is.
8. As a power user, I want Tab to complete file paths in the input prompt, so that I can type a partial path and finish it with one keystroke.
9. As any user, I want the input prompt to validate that the file exists and is readable before continuing, so that I am told about a typo immediately rather than four prompts later.

**Output handling**

10. As any user, I want the tool to propose an Auto-derived output path (e.g. `foo.pdf` → `foo-encrypted.pdf`), so that I do not have to type or invent a destination.
11. As any user, I want a final "Will write to X. OK? [Y/n]" confirmation, so that I can intervene to change the destination or cancel before any file is written.
12. As any user, I want the tool to refuse to overwrite an existing file silently — it must prompt for confirmation, so that I do not lose work to a name collision.
13. As any user, I want output filenames to never collide with the input (the tool must rename if the conventional output equals the input), so that an Operation never destroys its own source.

**Advanced options gating**

14. As a non-technical user, I want the default flow to ask only the essential questions, so that I am not overwhelmed by knobs whose meaning I do not understand.
15. As a power user, I want an "Advanced options? [y/N]" gate after the essential prompts, so that I can opt into the full knob set without it being thrust on me by default.

**Batch mode**

16. As a power user, I want to process many files in one Wizard run (e.g. encrypt 30 contracts at once), so that I do not have to relaunch the tool per file.
17. As a non-technical user, I want Batch mode to be opt-in via a "One file or many?" prompt, so that the single-file flow stays simple by default.
18. As any user in Batch mode, I want to see per-file progress and a summary of which files succeeded and which failed, so that I can spot and rerun the failures.

**Convert**

19. As any user, I want to convert a `.docx`, `.xlsx`, `.pptx`, `.odt`, `.rtf`, `.doc`, `.xls`, `.ppt`, `.ods`, or `.odp` file to PDF, so that I can share Office documents in a portable format.
20. As any user, I want the direction of conversion to be inferred from the input extension, so that converting from Office to PDF asks zero target-format questions.
21. As any user, I want to convert a PDF to a `.docx`, `.xlsx`, `.pptx`, or `.odt` file, so that I can re-edit a PDF in a word processor.
22. As any user, I want to convert a PDF to images (one PNG per page by default into a `<stem>-images/` directory), so that I can share individual pages as pictures.
23. As a power user, I want to pick JPEG instead of PNG and tune DPI/quality under Advanced options, so that I can trade file size for fidelity when needed.
24. As any user, I want to convert images (PNG, JPEG, TIFF, GIF) into a single PDF using the same loop-and-reorder input flow that Merge uses, so that I can stitch a scan into one document.
25. As any user, I want to convert a PDF to plain text, so that I can grep or paste its contents elsewhere.
26. As any user, I want the tool to refuse conversions that are not PDF-on-one-side (e.g. `.docx → .odt`) with a clear "this is `pdf-tool`, not a general format converter" message, so that the tool's scope is obvious.

**Encrypt / Decrypt**

27. As any user, I want to encrypt a PDF with a password, so that I can protect a sensitive document before sending it.
28. As any user, I want the password prompt to mask input and to ask for confirmation by re-entry, so that I cannot lock a document with a typo.
29. As a power user, I want to choose encryption strength (40 / 128 / 256-bit) and per-permission flags (print / copy / modify / annotate) under Advanced options, so that I can produce compliance-level outputs.
30. As any user, I want to decrypt a PDF I know the password for, so that I can remove a password from a document I own.
31. As any user, I want a wrong password during decrypt to surface as a plain "Wrong password" message, so that I know what to fix.

**Split**

32. As any user, I want to split a PDF into one file per page, so that I can extract individual pages as standalone PDFs.
33. As any user, I want to split a PDF every N pages, so that I can chunk a long document into evenly-sized parts.
34. As any user, I want to split a PDF at specific page boundaries (e.g. `5, 12, 20` produces files containing 1–4, 5–11, 12–19, 20–end), so that I can break it at logical sections.
35. As any user, I want to extract specific pages into one new PDF using the shared Page Selection widget, so that I can pull out the pages I care about.
36. As any user, I want split outputs to land in a `<stem>-pages/` directory next to the input, so that I do not litter the working directory with N files.

**Merge**

37. As any user, I want to merge multiple PDFs into one, so that I can assemble chapters or appendices into a single document.
38. As any user, I want to add input PDFs one at a time in a loop until I am done, so that I can build up the merge list without learning glob syntax.
39. As any user, I want to see the assembled order and reorder it before the merge runs, so that I can fix the order without restarting.
40. As any user, I want the merged output name to default to a sensible derivative (e.g. `<first-stem>-merged.pdf`), so that I do not need to invent a name.

**Rotate**

41. As any user, I want to rotate pages in a PDF, so that I can fix a scan that came out landscape-wrong.
42. As any user, I want to pick which pages to rotate via the shared Page Selection widget (All / Odd / Even / First N / Last N / Custom Range), so that I do not have to learn a separate syntax for each Operation.
43. As any user, I want 90° clockwise as the default rotation with 90° CCW and 180° as alternatives, so that the common case is one prompt.

**Compress**

44. As any user, I want to compress a PDF using a "good enough for email" default preset, so that I can shrink an oversized file with one prompt.
45. As a power user, I want to pick `/screen`, `/ebook`, `/printer`, or `/prepress` ghostscript presets and tune image DPI / JPEG quality under Advanced options, so that I can hit a specific size or quality target.
46. As any user, I want the tool to report the before / after file size after compression, so that I can see whether the operation was worthwhile.

**Inspect**

47. As any user, I want to inspect a PDF and see its page count, metadata (title, author, creator, dates), and encryption status without making any modifications, so that I can quickly understand a file I have just received.
48. As any user, I want Inspect to work on encrypted PDFs without requiring the password (it can report "encrypted, cannot read content" without failing), so that I can confirm whether a file is locked.

**OCR**

49. As any user, I want to add a searchable text layer to a scanned PDF, so that I can search and copy text from it.
50. As a power user, I want to pick the OCR language (default English) and force re-OCR under Advanced options, so that I can OCR non-English scans or re-process a PDF that already has a poor text layer.

**Watermark**

51. As any user, I want to add a text watermark to a PDF using a default centred-diagonal-grey-30%-opacity style, so that I can mark a document "DRAFT" or "CONFIDENTIAL" with one short prompt.
52. As a power user, I want to choose watermark text, position, opacity, colour, font, and target pages (via Page Selection) under Advanced options, so that I can produce branded watermarks.

**Metadata**

53. As any user, I want to view and edit a PDF's metadata fields (title, author, subject, keywords), so that I can clean up a file before sending it externally.
54. As any user, I want to strip all metadata in one action, so that I can sanitise a file before public release.

**Repair**

55. As any user, I want to attempt to repair a corrupted or malformed PDF, so that I have a fallback when another tool refuses to open it.
56. As any user, I want Repair to try `pikepdf` first and fall back to `ghostscript`, so that the lighter option is tried before the heavier one.

**Errors and Backend missing**

57. As a non-technical user, I want errors presented in plain English with a suggested next step (e.g. "This PDF is password-protected. Use Decrypt first."), so that I am not staring at a Python traceback or a libreoffice stderr dump.
58. As a power user, I want to rerun with `--debug` to get the raw Backend output, so that I can debug genuinely surprising failures.
59. As any user, I want the tool to not write any state to disk between runs (no logs, no recent-files cache, no last-directory file), so that there is no persistent surface that could leak document paths.

**Installation and distribution**

60. As a developer, I want to install via `pipx install pdf-tool`, so that I get an isolated install I can upgrade independently.
61. As a non-technical user, I want to install via `brew install <tap>/pdf-tool` (one command), so that I get the tool plus all system dependencies (libreoffice, ghostscript, ocrmypdf, tesseract) without managing them myself.
62. As any user on Linux, I want the same Homebrew formula to work on Linuxbrew, so that the install story is identical to macOS.

## Implementation Decisions

**Architecture.** Wrapper-shaped: `pikepdf` is the primary Backend; external binaries (libreoffice, ghostscript, ocrmypdf, pdftoppm/pdftotext, img2pdf) are secondary Backends invoked via subprocess. The full per-Operation Backend mapping and its alternatives are recorded in `docs/adr/0001-wrapper-architecture-pikepdf-primary.md`.

**Distribution.** Two channels: PyPI (`pipx install pdf-tool`) and a Homebrew tap (`brew install <user>/pdf-tool/pdf-tool`). The tap formula declares Python 3.12, libreoffice, ghostscript, ocrmypdf, and tesseract as dependencies. macOS and Linux supported; Windows explicitly out of scope.

**Wizard.** One-shot interactive flow on each invocation — no REPL, no persistent TUI, no state between runs. Built with `questionary` (prompts, tab-completion via the underlying `prompt_toolkit`), `rich` (formatted output and progress bars), and `typer` (the thin CLI shell around `--debug` and `--version`).

**Modules to build.** (All to be implemented from scratch; the repo is greenfield.)

*Deep, pure / near-pure modules — these are the testable spine of the tool.*

- **Range parser.** Surface: `parse(spec: str, n_pages: int) -> list[int]`. Accepts strings like `1-3,5,7-9`; rejects empty tokens, descending ranges, out-of-bounds pages, non-integer tokens, with structured exceptions. Pure; no I/O.
- **Auto-derived output namer.** Surface: `derive(input_path: Path, operation: OperationName, **opts) -> Path`. Encodes every Operation's naming convention (`-encrypted.pdf`, `-decrypted.pdf`, `-pages/` directory, `.docx`/`.png`/`.txt` extension swap for Convert, `-merged.pdf`, `-rotated.pdf`, `-compressed.pdf`, `-ocr.pdf`, `-watermarked.pdf`, `-repaired.pdf`). Pure; single place to change conventions.
- **Page Selection resolver.** Surface: `resolve(choice: PageSelection, n_pages: int) -> list[int]`. Turns a `PageSelection` value (`All` / `Odd` / `Even` / `FirstN(n)` / `LastN(n)` / `CustomRange(spec)`) into a concrete sorted list of pages. Wraps the Range parser for the custom case. Decoupled from the UI prompt that produces a `PageSelection`.
- **Backend probe.** Surface: `probe() -> BackendAvailability`. Returns a map of Backend → `Available | Missing(install_hint)` by calling `shutil.which` (and a version sniff where it matters, e.g. libreoffice ≥ 7). The Wizard runner consumes this to build the menu.
- **Error translator.** Surface: `translate(operation: OperationName, failure: BackendFailure) -> FriendlyError`. Holds the known-error table — wrong password, file not found, libreoffice "source format not supported", ocrmypdf "already has text", ghostscript exit codes, pikepdf `PasswordError` / `PdfError`. Falls back to a generic "{operation} failed. Rerun with `--debug` for details." Pure.

*Backend wrappers — the abstraction over the actual work.*

- **`PikepdfBackend`.** One class exposing `encrypt`, `decrypt`, `split_every_page`, `split_every_n`, `split_at_boundaries`, `extract_pages`, `merge`, `rotate`, `inspect`, `set_metadata`, `strip_metadata`, `watermark`, `try_repair`. Takes paths and option dataclasses, returns paths or info dicts. All pikepdf calls live here — no `import pikepdf` outside this module.
- **`SubprocessBackend` (base) + per-binary subclasses.** Base class handles argv construction shape, stderr capture, exit code, timeout, and produces a uniform `BackendFailure` on non-zero exit. Concrete subclasses: `LibreOfficeBackend` (Office↔PDF), `GhostscriptBackend` (compress, repair-fallback), `OcrmypdfBackend` (OCR), `PdftoppmBackend` (PDF→image), `PdftotextBackend` (PDF→text), `Img2pdfBackend` (image→PDF). Each subclass owns its own argv shape and a small recognised-error table that feeds the translator. No `subprocess.run` calls scattered through other modules.

*Operation handlers — one per Operation.*

- One module per Operation (Convert, Encrypt, Decrypt, Split, Merge, Rotate, Compress, Inspect, OCR, Watermark, Metadata, Repair). Each owns its prompt sequence (essentials + Advanced options gate), dispatches to the appropriate Backend, and reports the result via the Wizard runner. Thin plumbing.

*UI and orchestration.*

- **Wizard runner.** Top-level loop: probe → build menu (omitting / disabling operations whose Backend is missing) → prompt for operation → invoke handler → display result. Single entry point called by the CLI.
- **File input widget.** Reusable prompt that accepts a path with tab-completion, normalises drag-and-drop pasted paths (strip surrounding quotes, expand `~`), and validates existence/readability before returning. Returns a `Path`.
- **Batch loop.** Given an Operation handler and a list of inputs, runs the handler per input, reports per-file progress via `rich`, and prints a final outcome summary (succeeded / failed counts with the per-file error reason from the Error translator).
- **CLI entry point.** `typer` shell registering a single root command (no subcommands — explicit non-goal). Handles `--debug` / `--version` / `--help` and dispatches to the Wizard runner.

**Operation → Backend dispatch.** As specified in ADR-0001. Compress always goes to Ghostscript; Convert dispatches to LibreOffice (Office↔PDF), PdftoppmBackend (PDF→image), PdftotextBackend (PDF→text), or Img2pdf (image→PDF) based on extensions; OCR goes to ocrmypdf; all other Operations go to pikepdf.

**Defaults.**

- Encryption strength: AES-256 (pikepdf default for modern PDFs).
- OCR language: English (`eng`).
- PDF→image: PNG at 150 DPI.
- Compress: ghostscript `/ebook` preset.
- Rotate: 90° clockwise.
- Watermark: centred diagonal, 30% opacity, grey.
- All other knobs hidden behind the "Advanced options?" gate.

**Error handling surface.** Two paths: Friendly (default) and Debug (`--debug` flag or `PDF_TOOL_DEBUG=1`). Friendly suppresses Backend stderr unless exit code is non-zero, in which case the last 1–2 lines are appended under the translated message. No persistent log files in either mode.

**Persistence.** None. No `~/.pdf-tool/` directory. Each Wizard run is a clean slate.

## Testing Decisions

**What makes a good test in this codebase.** Test external behaviour, not internal structure. For pure modules, that means testing the function's contract: given inputs X, the return is Y; given malformed input, the function raises the documented exception. For Backend wrappers, that means feeding in real PDFs (small fixtures committed under `tests/fixtures/`) and asserting properties of the output PDF (page count, metadata, encryption status) — not asserting the precise libqpdf bytes. Tests do not reach into module internals, do not patch private functions, and do not assert on log messages or stdout formatting.

**Modules with required unit tests.**

- **Range parser** — exhaustive table-driven tests for valid syntax variations, plus a parallel table for each rejection case (empty tokens, descending ranges, out-of-bounds, non-integers, mixed separators). Pure function; easy to cover comprehensively.
- **Auto-derived output namer** — table-driven test covering each Operation's naming convention, including edge cases like input with no extension, input that already contains the suffix, input that would collide with a directory of the same name.
- **Page Selection resolver** — tests for each preset (`All` / `Odd` / `Even` / `FirstN` / `LastN`) against various page counts (1, 2, large), and for `CustomRange` delegating correctly to the Range parser. Boundary cases: `FirstN(n)` with `n > n_pages`, `LastN(0)`, `Odd` on a single-page document.
- **Backend probe** — tests with `shutil.which` patched to a stub map; assert that missing binaries produce the correct install-hint strings and that the available set reflects the stub.
- **Error translator** — table-driven tests: for each known `(Operation, BackendFailure)` shape (pikepdf `PasswordError`, libreoffice exit code 77 with specific stderr pattern, ocrmypdf "already has text", ghostscript exit code 1 with "invalid xref" stderr, etc.), assert the produced `FriendlyError` message and suggested action. Generic fallback case asserted as well.

**Modules with integration tests** (gated behind a `pytest -m integration` marker, skipped if the required binary is absent on the runner).

- **`PikepdfBackend`** — round-trip tests for each method against small fixture PDFs. Encrypt then decrypt yields the original; split then merge reconstructs the original; rotate twice by 180° is a no-op; metadata writes survive a re-open.
- **`SubprocessBackend` subclasses** — for each: a single happy-path test (input fixture, run, assert output exists and has plausible properties) and a single failure-path test (synthesise a known-bad input, assert the `BackendFailure` shape captures the right stderr and exit code).

**Modules without required tests** (shallow plumbing — manual smoke testing on first run is enough for v1).

- Operation handlers — they are thin glue; their behaviour is fully exercised when the wizard is driven manually.
- Wizard runner — same.
- File input widget — UI behaviour; manual.
- Batch loop — integration-tested via running an Operation handler with a list of two inputs.
- CLI entry point — `--version` and `--debug` toggling verified manually.

**Prior art.** None — the repo is greenfield. The conventions established by the first round of tests become the prior art. Recommend `pytest` + `pytest-mark` for the `integration` marker; fixtures committed under `tests/fixtures/` (small, public-domain PDFs only); golden files for inspect output stored as JSON next to the fixtures.

## Out of Scope

- **Scripted / non-interactive use.** No subcommands, no flag-driven operations (e.g. `pdf-tool encrypt foo.pdf --password ...` is explicitly not a goal). The tool's contract is "launch, prompt, exit". `--debug`, `--version`, `--help` are the only flags.
- **Windows support.** The Wizard, drag-and-drop, Homebrew install path, and external-binary install instructions all assume macOS or Linux. Revisit when there is concrete demand.
- **Persistent state.** No `~/.pdf-tool/` directory, no recent files, no last-used directory, no log files. Drag-and-drop and tab-completion absorb the cost of path entry.
- **Office-to-Office and Image-to-Image conversion.** Convert requires PDF on one side. LibreOffice technically supports `.docx → .odt`, but it is not in scope — the tool is `pdf-tool`, not a general format converter.
- **PDF signing.** No digital signatures, no certificate management. Out of scope for v1.
- **Form filling and form data extraction.** Niche relative to the audience; deferred.
- **Persistent log files.** Specifically rejected for privacy reasons (paths to personal documents end up on disk).
- **A `--doctor` command separate from the startup probe.** The startup probe already shows missing-Backend hints in-menu; a separate command is redundant.

## Further Notes

- The full architectural rationale (including rejected alternatives like pure shell-out, pure native Python, `pypdf` instead of `pikepdf`, and `pdfcpu`) lives in `docs/adr/0001-wrapper-architecture-pikepdf-primary.md`. Refer there before reopening any of those questions.
- `CONTEXT.md` is the canonical glossary. Implementation should match the language there — particularly Operation, Backend, Wizard, Batch mode, Advanced options, Page Selection, Split Mode, Auto-derived output, and Friendly / Debug path.
- Suggested project layout (greenfield, so this is a starting point, not a constraint): `pdf_tool/cli.py` (typer entry), `pdf_tool/wizard.py` (runner), `pdf_tool/operations/<op>.py` (handlers), `pdf_tool/backends/pikepdf_backend.py` and `pdf_tool/backends/<binary>_backend.py` (wrappers), `pdf_tool/widgets/file_input.py` and `pdf_tool/widgets/page_selection.py` (UI), `pdf_tool/core/range_parser.py`, `pdf_tool/core/output_namer.py`, `pdf_tool/core/probe.py`, `pdf_tool/core/error_translator.py` (the deep pure modules), `tests/` (mirroring the package), `tests/fixtures/` (sample PDFs).
- First milestone for implementation: scaffolding + Range parser + Auto-derived output namer + Page Selection resolver + Backend probe + a single Operation (Encrypt is a natural pick — `pikepdf` only, no shell-out, short prompt set). Each subsequent Operation slots in via the same shape.

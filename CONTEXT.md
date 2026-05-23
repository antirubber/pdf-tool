# PDF Tool

An interactive wizard-style CLI for everyday PDF manipulation — convert, encrypt, split, merge, rotate, compress, inspect, OCR, watermark, edit metadata, repair — aimed at personal use and terminal-curious non-technical users on macOS and Linux.

## Language

**Operation**:
One of the eleven things the user can pick from the Wizard's top-level menu (Convert, Encrypt, Decrypt, Split, Merge, Rotate, Compress, Inspect, OCR, Watermark, Metadata, Repair). The unit of work selected per Wizard run.
_Avoid_: action, command, function, task

**Backend**:
The underlying tool that performs the actual work for an Operation. `pikepdf` is the primary Backend (covers encrypt/decrypt/split/merge/rotate/inspect/metadata/watermark); `libreoffice`, `ghostscript`, `ocrmypdf`, `poppler` (`pdftoppm`, `pdftotext`), `img2pdf` are secondary Backends for ops `pikepdf` can't do natively.
_Avoid_: engine, driver, helper. Note: distinct from **Dependency**, which includes Python libs and OS packages more broadly.

**Wizard**:
The one-shot interactive flow: launch → menu → prompts → execute → exit. Not a REPL and not a persistent TUI — each invocation runs exactly one Operation and terminates.
_Avoid_: REPL, session, shell

**Batch mode**:
Opt-in mode within an Operation where one Wizard run processes N input files instead of one. Default is single-file; Batch mode is reached by answering "many" to the "One file or many?" prompt.
_Avoid_: bulk mode, multi-file mode

**Advanced options**:
The optional second tier of prompts shown only when the user opts in via the "Advanced options? [y/N]" gate. Hides knobs (encryption strength, DPI, JPEG quality, compress preset, watermark position) that defaults handle for the common case.
_Avoid_: expert mode, power mode

**Page Selection**:
The shared widget for "operate on which pages". Presents presets (All / Odd / Even / First N / Last N) with a Custom Range escape that takes a `1-3,5,7-9` string. Used by Rotate, Watermark, Metadata, and Split's "extract" Split Mode.
_Avoid_: page picker, page filter

**Split Mode**:
The partition strategy chosen inside the Split Operation: `every-page` / `every-N-pages` / `at-boundaries` / `extract-pages-into-one`. Distinct from Page Selection — Split Mode decides how to partition the input into outputs; Page Selection picks a subset of pages to operate on.
_Avoid_: split type, split strategy

**Auto-derived output**:
The default convention where output paths are inferred from the input path (`foo.pdf` → `foo-encrypted.pdf`, `foo.pdf` → `foo-pages/` for Split, `foo.pdf` → `foo.docx` for Convert). The user sees the derived path in a final "Will write to X. OK? [Y/n]" confirmation and can override there.
_Avoid_: default output, output convention

**Friendly path / Debug path**:
The two error-display modes. Friendly path (default) shows plain-English messages mapped from known Backend errors via a translation table; Backend stderr is suppressed unless exit code ≠ 0. Debug path (`--debug` or `PDF_TOOL_DEBUG=1`) shows raw Backend output and full tracebacks. No persistent log files in either mode.
_Avoid_: verbose mode, quiet mode

## Example dialogue

> **Dev:** When the user picks Rotate, do we show Page Selection before or after the rotation angle?
>
> **Domain:** Page Selection first — it follows the file input prompt, same as every other Operation that targets a subset of pages. Rotation angle is an Operation-specific prompt that comes after.
>
> **Dev:** And if they pick the Custom Range escape inside Page Selection?
>
> **Domain:** They get a single text prompt that accepts `1-3,5,7-9` syntax with inline format help. Same widget, same syntax, every Operation that uses Page Selection.
>
> **Dev:** What about Split — does it use Page Selection?
>
> **Domain:** Only the `extract-pages-into-one` Split Mode does. The other three Split Modes (`every-page`, `every-N-pages`, `at-boundaries`) partition the whole input, so Page Selection doesn't apply — they have their own prompts (e.g. "Split every how many pages?").

## Flagged ambiguities

None currently. Resolve here when terminology conflicts surface.

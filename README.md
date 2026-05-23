# pdf-tool

Interactive wizard CLI for everyday PDF manipulation — encrypt, decrypt, split, merge, rotate, compress, inspect, OCR, watermark, edit metadata, repair, convert — aimed at terminal-curious users on macOS and Linux.

## Install

```bash
pipx install pdf-tool
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install .
```

## Usage

```bash
pdf-tool                # launch the wizard
pdf-tool --version      # show version
pdf-tool --debug        # show raw backend output and tracebacks
```

The wizard presents a menu of operations, prompts for what it needs, and exits. No subcommands, no flags to memorize.

Operations whose required backends are missing appear greyed-out with install hints.

## System dependencies

| Operation | Needs | Install |
|---|---|---|
| Compress | Ghostscript | `brew install ghostscript` |
| Convert (Office ↔ PDF) | LibreOffice | `brew install libreoffice` |
| Convert (PDF → images) | poppler | `brew install poppler` |
| Convert (PDF → text) | poppler | `brew install poppler` |
| Convert (images → PDF) | img2pdf | `brew install img2pdf` |
| OCR | ocrmypdf | `brew install ocrmypdf` |

Encrypt, decrypt, split, merge, rotate, inspect, watermark, metadata, and repair need only `pikepdf` (installed automatically with the package).

## Development

```bash
uv sync --dev           # create venv, install runtime + dev deps
uv run pytest           # run tests
uv run pdf-tool         # run from source
```

## License

MIT

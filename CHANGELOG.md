# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and the project adheres to
[Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-06-16

### Added
- New Transform Operations: Remove pages, Reorder pages, and Page numbers
  (with a Bates style in Advanced).
- Encrypt Advanced options: encryption strength (AES-256/128/40-bit RC4) and
  per-permission flags (print, copy, modify, annotate).
- Inspect now also reports file size, PDF version, first-page dimensions with
  a derived label (e.g. "A4 portrait"), and text-layer presence.
- Encrypted inputs prompt for a password inline instead of aborting, across the
  page-targeting Operations.
- Batch mode extended to Rotate, Decrypt, Watermark, OCR, and Metadata strip.
- Progress spinners on slow Operations and live per-file status in Batch.
- Output ergonomics: pre-flight recap, a closing summary panel, and a
  page-count echo after the input is chosen.
- Post-run conveniences (open/reveal output, copy path) and a
  `pdf-tool completion [bash|zsh|fish]` subcommand.
- Errors now show the suggested next step, with install hints localized to the
  detected package manager (apt/dnf/pacman/brew).

### Fixed
- pikepdf/OS errors are translated to friendly messages at the Backend
  boundary; `--debug` still shows the full traceback.
- Subprocess Backends write output atomically (no partial file on failure).
- Friendly "timed out" message; Merge/Split carry forward the highest source
  PDF version.
- Page ranges are bound-checked before expansion (no OOM on `1-2000000000`).
- Empty Encrypt passwords are rejected; Metadata Edit can clear a field and
  Strip purges the trailer `/ID` and XMP.
- Decrypt detects an already-unencrypted PDF; Watermark sizes/positions per
  page; `ensure_unique` names dotted directory outputs correctly.
- Convert runs in an isolated temp dir so LibreOffice cannot clobber a
  same-stem file; drag-and-drop paths (`file://`, escaped spaces) resolve, and
  existing destinations prompt before overwriting.
- The version is single-sourced across `pyproject`, `__init__`, and the tag.

### Security
- Ghostscript runs with `-dSAFER`, with a startup version probe.
- LibreOffice runs in a throwaway profile with macros disabled.
- `install.sh` validates the release ref; `pdf-tool update` verifies the
  installer's published SHA256 before executing it (see ADR-0002).

### Changed
- UI polish: accented menu group headers, clearer unavailable rows, and
  consistent sentence-case prompt copy.

## [0.1.0] - 2026-06-04

### Added
- `pdf-tool update` — re-runs the installer to update to the latest release.
- Release-based distribution: the installer now installs the latest published
  GitHub Release (falling back to master HEAD when no release exists yet) and
  skips reinstalling when already on the latest version.
- Distinct owner/user passwords for encryption.
- GitHub Actions release workflow and a `make release VERSION=X.Y.Z` helper.

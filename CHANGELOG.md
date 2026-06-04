# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and the project adheres to
[Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-06-04

### Added
- `pdf-tool update` — re-runs the installer to update to the latest release.
- Release-based distribution: the installer now installs the latest published
  GitHub Release (falling back to master HEAD when no release exists yet) and
  skips reinstalling when already on the latest version.
- Distinct owner/user passwords for encryption.
- GitHub Actions release workflow and a `make release VERSION=X.Y.Z` helper.

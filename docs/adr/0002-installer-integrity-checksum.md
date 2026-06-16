# Installer integrity via published SHA256 checksums

## Status

Accepted.

## Context

The install one-liner and `pdf-tool update` fetched a remote shell script and
piped it straight into `sh` with no integrity verification, and the bootstrap
fetches the `uv` installer the same way. A network attacker (or a compromised
host serving the raw file) could substitute arbitrary code that runs on the
user's machine. We need an integrity strategy before the fetched code executes.

## Decision

Ship **checksum-only** integrity for our own installer:

- Every release publishes `install.sh` and a `SHA256SUMS` file as release
  assets (see `.github/workflows/release.yml`). The assets are pinned to the
  immutable release tag, not a moving branch.
- `pdf-tool update` downloads `install.sh` and `SHA256SUMS` from the latest
  release, verifies the SHA256 of the script against the published digest, and
  **only executes the script if the digest matches** — it fails closed
  otherwise.
- The README documents a manual verify-then-run path for users who install by
  hand, using the same published `SHA256SUMS`.

Signature verification (minisign/cosign) is deliberately **deferred**: it adds
a maintainer key to generate, protect, and rotate, and a verification tool the
user must install. Checksums published over HTTPS by GitHub Releases raise the
bar meaningfully (the artifact and its digest are pinned and tamper-evident)
without that operational burden. Revisit if we gain a release-signing setup.

The `uv` bootstrap (`curl https://astral.sh/uv/install.sh | sh`) remains a
separate trust anchor owned by Astral; verifying it is out of scope here.

## Consequences

- Each release must carry the `install.sh` and `SHA256SUMS` assets; a release
  missing them makes `pdf-tool update` fail closed rather than run unverified.
- The verification logic lives in `pdf_tool/updater.py` and is unit-tested with
  injected fetchers (digest match, mismatch, and missing-download all covered).
- Users on the first (asset-less) release must reinstall via the one-liner once;
  every subsequent `update` is verified.

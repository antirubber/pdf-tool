#!/bin/sh
# Cut a release: bump the version, commit, tag, push. Pushing the tag fires
# .github/workflows/release.yml, which publishes the GitHub Release that the
# installer (and `pdf-tool update`) resolve via the releases/latest API.
#
# Usage: scripts/release.sh 0.1.0
set -eu

VERSION="${1:?usage: scripts/release.sh X.Y.Z}"
INIT="pdf_tool/__init__.py"

case "$VERSION" in
    [0-9]*.[0-9]*.[0-9]*) ;;
    *) echo "version must look like X.Y.Z (got: $VERSION)" >&2; exit 1 ;;
esac

if [ -n "$(git status --porcelain)" ]; then
    echo "working tree is dirty; commit or stash first." >&2
    exit 1
fi

sed -i.bak "s/^__version__ = .*/__version__ = \"$VERSION\"/" "$INIT"
rm -f "$INIT.bak"

git add "$INIT"
git commit -m "Release v$VERSION"
git tag "v$VERSION"
git push
git push origin "v$VERSION"

echo "Pushed v$VERSION. The release workflow will publish the GitHub Release."

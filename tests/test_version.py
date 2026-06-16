import importlib.metadata

import pdf_tool


def test_version_is_single_sourced():
    # --version (reads __version__), installed package metadata, and the git
    # tag must all agree; metadata is derived from __init__ via hatch dynamic.
    assert importlib.metadata.version("pdf-tool") == pdf_tool.__version__

from pdf_tool.core.probe import Available, BackendName, Missing, probe


def test_libreoffice_available_when_which_finds_it():
    found = {"libreoffice": "/usr/bin/libreoffice"}
    result = probe(which=found.get)
    assert result[BackendName.LIBREOFFICE] == Available()


def test_libreoffice_missing_carries_install_hint():
    result = probe(which=lambda _: None)
    assert result[BackendName.LIBREOFFICE] == Missing(
        install_hint="brew install libreoffice"
    )


def test_libreoffice_found_via_soffice_alias():
    found = {"soffice": "/Applications/LibreOffice.app/Contents/MacOS/soffice"}
    result = probe(which=found.get)
    assert result[BackendName.LIBREOFFICE] == Available()


def test_all_backends_reported_when_present():
    found = {
        "soffice": "/usr/bin/soffice",
        "gs": "/usr/bin/gs",
        "ocrmypdf": "/usr/bin/ocrmypdf",
        "pdftoppm": "/usr/bin/pdftoppm",
        "pdftotext": "/usr/bin/pdftotext",
        "img2pdf": "/usr/bin/img2pdf",
    }
    result = probe(which=found.get)
    assert result == {
        BackendName.LIBREOFFICE: Available(),
        BackendName.GHOSTSCRIPT: Available(),
        BackendName.OCRMYPDF: Available(),
        BackendName.PDFTOPPM: Available(),
        BackendName.PDFTOTEXT: Available(),
        BackendName.IMG2PDF: Available(),
        BackendName.PIKEPDF: Available(),
    }


def test_all_backends_missing_carry_install_hints():
    result = probe(which=lambda _: None)
    assert result == {
        BackendName.LIBREOFFICE: Missing(install_hint="brew install libreoffice"),
        BackendName.GHOSTSCRIPT: Missing(install_hint="brew install ghostscript"),
        BackendName.OCRMYPDF: Missing(install_hint="brew install ocrmypdf"),
        BackendName.PDFTOPPM: Missing(install_hint="brew install poppler"),
        BackendName.PDFTOTEXT: Missing(install_hint="brew install poppler"),
        BackendName.IMG2PDF: Missing(install_hint="brew install img2pdf"),
        BackendName.PIKEPDF: Available(),
    }


def test_install_hint_uses_apt_when_apt_present():
    # Backends all missing, but apt-get is on PATH → Debian-style hints.
    found = {"apt-get": "/usr/bin/apt-get"}
    result = probe(which=found.get)
    assert result[BackendName.GHOSTSCRIPT] == Missing(
        install_hint="sudo apt install ghostscript"
    )
    assert result[BackendName.PDFTOPPM] == Missing(
        install_hint="sudo apt install poppler-utils"
    )


def test_install_hint_uses_pacman_when_pacman_present():
    found = {"pacman": "/usr/bin/pacman"}
    result = probe(which=found.get)
    assert result[BackendName.LIBREOFFICE] == Missing(
        install_hint="sudo pacman -S libreoffice-fresh"
    )


def test_mixed_presence():
    found = {"gs": "/usr/bin/gs", "img2pdf": "/usr/bin/img2pdf"}
    result = probe(which=found.get)
    assert result[BackendName.GHOSTSCRIPT] == Available()
    assert result[BackendName.IMG2PDF] == Available()
    assert isinstance(result[BackendName.LIBREOFFICE], Missing)
    assert isinstance(result[BackendName.OCRMYPDF], Missing)
    assert isinstance(result[BackendName.PDFTOPPM], Missing)
    assert isinstance(result[BackendName.PDFTOTEXT], Missing)


def test_probe_defaults_to_shutil_which():
    result = probe()
    assert result[BackendName.PIKEPDF] == Available()
    assert set(result.keys()) == set(BackendName)

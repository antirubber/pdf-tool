ALL_DEPS = ("gs", "pdftoppm", "img2pdf")
REPO = "git+https://github.com/antirubber/pdf-tool.git"


def test_installs_tool_with_uv_when_deps_present(run_install):
    result = run_install(
        os_name="Darwin", present=("uv", *ALL_DEPS)
    )
    runs = result.of_kind("RUN")
    assert any(
        "uv tool install" in cmd
        and "git+https://github.com/antirubber/pdf-tool.git" in cmd
        for cmd in runs
    ), result.stdout


def test_falls_back_to_pipx_when_no_uv(run_install):
    result = run_install(present=("pipx", *ALL_DEPS))
    runs = result.of_kind("RUN")
    assert any("pipx install" in cmd and REPO in cmd for cmd in runs), result.stdout
    assert not any("uv tool install" in cmd for cmd in runs), result.stdout


def test_present_deps_are_skipped(run_install):
    result = run_install(present=("uv", *ALL_DEPS))
    skipped = result.of_kind("SKIP")
    assert set(skipped) == {"ghostscript", "poppler", "img2pdf"}, result.stdout


def test_macos_brew_installs_missing_deps(run_install):
    result = run_install(os_name="Darwin", present=("brew", "uv"))
    runs = result.of_kind("RUN")
    assert "brew install ghostscript poppler img2pdf" in runs, result.stdout


def test_linux_apt_needs_root_so_prints_manual(run_install):
    result = run_install(os_name="Linux", uid=1000, present=("apt-get", "uv"))
    manual = result.of_kind("MANUAL")
    assert "sudo apt-get install -y ghostscript poppler-utils img2pdf" in manual, (
        result.stdout
    )
    # nothing auto-runs the system install when elevation is needed
    assert not any("apt-get install" in cmd for cmd in result.of_kind("RUN")), (
        result.stdout
    )


def test_linux_dnf_manual_command(run_install):
    result = run_install(os_name="Linux", uid=1000, present=("dnf", "uv"))
    assert "sudo dnf install -y ghostscript poppler-utils img2pdf" in result.of_kind(
        "MANUAL"
    ), result.stdout


def test_linux_pacman_keeps_poppler_name(run_install):
    result = run_install(os_name="Linux", uid=1000, present=("pacman", "uv"))
    assert (
        "sudo pacman -S --noconfirm ghostscript poppler img2pdf"
        in result.of_kind("MANUAL")
    ), result.stdout


def test_linux_root_runs_without_sudo(run_install):
    result = run_install(os_name="Linux", uid=0, present=("apt-get", "uv"))
    assert "apt-get install -y ghostscript poppler-utils img2pdf" in result.of_kind(
        "RUN"
    ), result.stdout
    assert result.of_kind("MANUAL") == [], result.stdout


def test_brew_as_root_is_an_error(run_install):
    result = run_install(os_name="Darwin", uid=0, present=("brew", "uv"))
    errors = result.of_kind("ERROR")
    assert any("root" in msg.lower() for msg in errors), result.stdout
    assert not any("brew install" in cmd for cmd in result.of_kind("RUN")), (
        result.stdout
    )


def test_no_package_manager_prints_manual_guidance(run_install):
    result = run_install(os_name="Linux", uid=1000, present=("uv",))
    manual = result.of_kind("MANUAL")
    assert any(
        "ghostscript" in m and "poppler" in m and "img2pdf" in m for m in manual
    ), result.stdout


def test_exit_zero_when_fully_automatable(run_install):
    result = run_install(os_name="Darwin", present=("uv", *ALL_DEPS))
    assert result.returncode == 0, result.stdout


def test_nonzero_exit_when_action_remains(run_install):
    result = run_install(os_name="Linux", uid=1000, present=("apt-get", "uv"))
    assert result.returncode != 0, result.stdout


def test_real_run_executes_the_install(run_install):
    # All deps present; the only step is the tool install, served by a stub uv
    # that exits 0. A non-dry run must actually invoke it and succeed.
    result = run_install(
        os_name="Darwin", present=("uv", *ALL_DEPS), dry_run=False
    )
    assert result.returncode == 0, result.stdout
    assert "uv tool install" in result.stdout, result.stdout
    # Real-run output is human-facing, not the machine plan format.
    assert "RUN " not in result.stdout, result.stdout


def test_bootstraps_uv_when_no_installer_present(run_install):
    result = run_install(present=ALL_DEPS)
    runs = result.of_kind("RUN")
    assert any("astral.sh/uv/install.sh" in cmd for cmd in runs), result.stdout
    assert any("uv tool install" in cmd and REPO in cmd for cmd in runs), result.stdout


def test_installs_latest_release_tag_when_one_exists(run_install):
    result = run_install(
        os_name="Darwin",
        present=("uv", "curl", *ALL_DEPS),
        stub_bodies={"curl": 'echo \'{"tag_name": "v0.1.0"}\''},
    )
    runs = result.of_kind("RUN")
    assert any(f"uv tool install --force {REPO}@v0.1.0" == cmd for cmd in runs), (
        result.stdout
    )


def test_metacharacter_tag_is_refused_and_falls_back_to_master(run_install):
    result = run_install(
        os_name="Darwin",
        present=("uv", "curl", *ALL_DEPS),
        stub_bodies={"curl": "echo '{\"tag_name\": \"v0.1.0; rm -rf ~\"}'"},
    )
    runs = result.of_kind("RUN")
    # The hostile tag must never be interpolated into the install command.
    assert not any("rm -rf" in cmd for cmd in runs), result.stdout
    # It falls back to the bare repo (no @tag).
    assert any("uv tool install" in cmd for cmd in runs), result.stdout
    assert not any("@v0.1.0" in cmd for cmd in runs), result.stdout


def test_falls_back_to_master_when_no_release(run_install):
    # curl present but the API returns nothing → install the bare repo, no @tag.
    result = run_install(
        os_name="Darwin",
        present=("uv", "curl", *ALL_DEPS),
        stub_bodies={"curl": "exit 0"},
    )
    runs = result.of_kind("RUN")
    assert any("uv tool install" in cmd for cmd in runs), result.stdout
    assert not any("@v" in cmd for cmd in runs), result.stdout


def test_skips_install_when_already_on_latest_release(run_install):
    result = run_install(
        os_name="Darwin",
        present=("uv", "curl", "pdf-tool", *ALL_DEPS),
        stub_bodies={
            "curl": 'echo \'{"tag_name": "v0.1.0"}\'',
            "pdf-tool": 'echo "pdf-tool 0.1.0"',
        },
    )
    assert "pdf-tool v0.1.0" in result.of_kind("SKIP"), result.stdout
    assert not any("tool install" in cmd for cmd in result.of_kind("RUN")), (
        result.stdout
    )

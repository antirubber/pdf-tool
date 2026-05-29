#!/bin/sh
# pdf-tool installer.

REPO="git+https://github.com/antirubber/pdf-tool.git"

DRY_RUN=0
[ "$1" = "--dry-run" ] && DRY_RUN=1

PENDING=0
plan() {
    kind="$1"
    payload="$2"
    case "$kind" in
        MANUAL|ERROR) PENDING=1 ;;
    esac

    if [ "$DRY_RUN" -eq 1 ]; then
        # Machine-readable plan (the tested contract).
        echo "$kind $payload"
        return
    fi

    # Human-facing execution.
    case "$kind" in
        SKIP)   echo "  ✓ $payload already installed" ;;
        MANUAL) echo "  ⚠ run this yourself:  $payload" ;;
        ERROR)  echo "  ✗ $payload" ;;
        RUN)
            echo "  → $payload"
            if ! eval "$payload"; then
                echo "  ✗ command failed: $payload"
                PENDING=1
            fi
            ;;
    esac
}

# Probe binary that proves a dep is installed.
probe_binary() {
    case "$1" in
        ghostscript) echo gs ;;
        poppler)     echo pdftoppm ;;
        img2pdf)     echo img2pdf ;;
    esac
}

# Package name for a dep under a given package manager.
pkg_name() {
    # $1 = manager, $2 = dep
    case "$1:$2" in
        *:ghostscript)        echo ghostscript ;;
        *:img2pdf)            echo img2pdf ;;
        apt-get:poppler|dnf:poppler) echo poppler-utils ;;
        *:poppler)            echo poppler ;;
    esac
}

# Base install command for a manager (packages appended by caller).
install_cmd() {
    case "$1" in
        brew)    echo "brew install" ;;
        apt-get) echo "apt-get install -y" ;;
        dnf)     echo "dnf install -y" ;;
        pacman)  echo "pacman -S --noconfirm" ;;
    esac
}

# --- system dependencies ---------------------------------------------------
MISSING=""
for dep in ghostscript poppler img2pdf; do
    if command -v "$(probe_binary "$dep")" >/dev/null 2>&1; then
        plan SKIP "$dep"
    else
        MISSING="$MISSING $dep"
    fi
done

if [ -n "$MISSING" ]; then
    # Select a package manager.
    MANAGER=""
    if [ "$(uname)" = "Darwin" ]; then
        command -v brew >/dev/null 2>&1 && MANAGER=brew
    else
        for m in apt-get dnf pacman brew; do
            if command -v "$m" >/dev/null 2>&1; then
                MANAGER="$m"
                break
            fi
        done
    fi

    if [ -n "$MANAGER" ]; then
        pkgs=""
        for dep in $MISSING; do
            pkgs="$pkgs $(pkg_name "$MANAGER" "$dep")"
        done
        cmd="$(install_cmd "$MANAGER")$pkgs"

        # brew never needs (and refuses) root; native managers need it.
        if [ "$MANAGER" = brew ]; then
            if [ "$(id -u)" -eq 0 ]; then
                plan ERROR "Homebrew refuses to run as root; re-run as a normal user."
            else
                plan RUN "$cmd"
            fi
        elif [ "$(id -u)" -eq 0 ]; then
            plan RUN "$cmd"
        else
            plan MANUAL "sudo $cmd"
        fi
    else
        plan MANUAL "install these with your package manager:$MISSING"
    fi
fi

# --- install the tool ------------------------------------------------------
if command -v uv >/dev/null 2>&1; then
    plan RUN "uv tool install $REPO"
elif command -v pipx >/dev/null 2>&1; then
    plan RUN "pipx install $REPO"
else
    plan RUN "curl -LsSf https://astral.sh/uv/install.sh | sh"
    # The uv installer drops the binary in ~/.local/bin, not yet on PATH.
    plan RUN 'export PATH="$HOME/.local/bin:$PATH"'
    plan RUN "uv tool install $REPO"
fi

if [ "$DRY_RUN" -eq 0 ]; then
    if [ "$PENDING" -eq 0 ]; then
        echo "Done. Run 'pdf-tool' to start."
    else
        echo "Some steps above need your attention; re-run when they're done."
    fi
fi

exit "$PENDING"

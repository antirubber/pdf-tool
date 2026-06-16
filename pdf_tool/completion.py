_BASH = """\
# pdf-tool bash completion. Add to ~/.bashrc:
#   eval "$(pdf-tool completion bash)"
_pdf_tool_completion() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    COMPREPLY=( $(compgen -W "update completion --version --debug --help" -- "$cur") )
}
complete -F _pdf_tool_completion pdf-tool
"""

_ZSH = """\
#compdef pdf-tool
# pdf-tool zsh completion. Add to ~/.zshrc:
#   eval "$(pdf-tool completion zsh)"
_pdf_tool() {
    _arguments '1: :(update completion)' '--version[Show version and exit]' \\
        '--debug[Show raw Backend output and tracebacks]' '--help[Show help]'
}
compdef _pdf_tool pdf-tool
"""

_FISH = """\
# pdf-tool fish completion. Add to ~/.config/fish/config.fish:
#   pdf-tool completion fish | source
complete -c pdf-tool -f
complete -c pdf-tool -n __fish_use_subcommand -a update -d 'Update to the latest release'
complete -c pdf-tool -n __fish_use_subcommand -a completion -d 'Print a completion script'
complete -c pdf-tool -l version -d 'Show version and exit'
complete -c pdf-tool -l debug -d 'Show raw Backend output and tracebacks'
complete -c pdf-tool -l help -d 'Show help'
"""

_SCRIPTS = {"bash": _BASH, "zsh": _ZSH, "fish": _FISH}

SUPPORTED_SHELLS = tuple(_SCRIPTS)


def script_for(shell: str) -> str | None:
    """Completion script for ``shell`` (bash/zsh/fish), or None if unsupported."""
    return _SCRIPTS.get(shell)

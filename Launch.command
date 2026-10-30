#!/bin/zsh
cd "$(dirname "$0")" || exit 1
if command -v uv >/dev/null 2>&1; then
    uv run python main.py
elif [ -x /opt/homebrew/bin/uv ]; then
    /opt/homebrew/bin/uv run python main.py
else
    echo "Please install uv, then follow README.md."
    read -r "reply?Press Enter to close."
fi

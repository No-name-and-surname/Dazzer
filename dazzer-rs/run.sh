#!/usr/bin/env bash
# Скрипт для запуска Rust фаззера на NixOS

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Запуск Dazzer (Rust версия) ==="
echo ""

# Проверка наличия shell.nix
if [ -f "shell.nix" ]; then
    echo "Используется shell.nix для окружения..."
    nix-shell --run "cargo run"
else
    echo "Используется временное окружение nix-shell..."
    nix-shell -p rustc cargo --run "cargo run"
fi


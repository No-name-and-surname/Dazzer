{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    rustc
    cargo
    # Дополнительные инструменты для разработки
    rustfmt
    clippy
  ];
  
  shellHook = ''
    echo "Rust environment loaded!"
    echo "Rust version: $(rustc --version)"
    echo "Cargo version: $(cargo --version)"
  '';
}


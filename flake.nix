{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    nixpkgs,
    flake-utils,
    ...
  }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python3;
      in {
        devShells.default = pkgs.mkShell {
          packages = [
            python
            pkgs.uv
            pkgs.pyright
            pkgs.ruff
          ];

          shellHook = ''
            set -euo pipefail

            VENV_DIR=".venv"
            PYBIN="${python}/bin/python"

            if [[ ! -f pyproject.toml ]]; then
              echo "[uv] no pyproject.toml → initializing"
              uv init --python "$PYBIN"
            fi

            if [[ ! -d "$VENV_DIR" ]]; then
              echo "[uv] creating $VENV_DIR with $("$PYBIN" -V)"
              uv venv --python "$PYBIN" "$VENV_DIR"
            fi

            export VIRTUAL_ENV="$PWD/$VENV_DIR"
            export PATH="$VIRTUAL_ENV/bin:$PATH"

            if [[ -f uv.lock ]]; then
              echo "[uv] syncing (frozen)"
              uv sync --frozen || uv sync
            elif [[ -f requirements.txt ]]; then
              echo "[uv] installing from requirements.txt"
              uv pip install -r requirements.txt
              uv lock
            elif [[ -f pyproject.toml ]]; then
              echo "[uv] syncing from pyproject.toml"
              uv sync
            fi

            echo "[uv] ready → $(command -v python) → $(python -V)"
          '';
        };
      }
    );
}

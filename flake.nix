{
  description = "Sandbox to test usage of `earthkit-data` in eccharts";

  inputs = {
    nixpkgs.url = "nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";

    ecmwf.url = "github:carletes/ecmwf-nixpkgs";
    ecmwf.inputs.nixpkgs.follows = "nixpkgs";
    ecmwf.inputs.flake-utils.follows = "flake-utils";
  };


  outputs = { nixpkgs, flake-utils, ecmwf, ... }:
    (
      flake-utils.lib.eachDefaultSystem (system:
        let
          pkgs = import nixpkgs {
            inherit system;
            overlays = [
              ecmwf.overlays.default
            ];
          };
        in
        {
          devShells.default = pkgs.mkShell {
            buildInputs = with pkgs; [
              (eccodes.overrideAttrs (prev: rec {
                version = "2.41.0";
                src = (prev.src.override {
                  rev = version;
                  sha256 = "sha256-QjQPf+7XLr/vX+01ZLFx5WNwh2C0MxhKz7Gt4auPUz0=";
                });
              }))
            ];

            shellHook = ''
              if [ ! -r .venv/.done ]; then
                uv venv
                uv sync --frozen
                touch .venv/.done
              fi
              . ./.venv/bin/activate
            '';
          };
        }
      )
    );
}

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
          eccodes = (pkgs.eccodes.overrideAttrs (prev: rec {
            version = "2.41.0";
            src = (prev.src.override {
              rev = version;
              sha256 = "sha256-5MwEeH6JQTeTSfe9xPAB2BMDT102ZM+rDaVaBggV18s=";
            });
          }));
          libraryPath = with pkgs; lib.makeLibraryPath [
            # Numpy needs to load the zlib shared library.
            zlib

            # Package `eccodes-python` needs to load the eccodes share library.
            eccodes
          ];
        in
        {
          devShells.default = pkgs.mkShell {
            buildInputs = [
              eccodes
              pkgs.python313
              pkgs.uv
            ];

            shellHook = ''
              if [ ! -r .venv/.done ]; then
                uv venv
                uv sync --frozen
                touch .venv/.done
              fi
              . ./.venv/bin/activate
              export LD_LIBRARY_PATH="${libraryPath}"
              export DYLD_LIBRARY_PATH="${libraryPath}"
            '';
          };
        }
      )
    );
}

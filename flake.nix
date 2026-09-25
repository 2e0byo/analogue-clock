{
  description = "A very basic flake";

  inputs = {
    nixpkgs.url = "https://channels.nixos.org/nixpkgs-unstable/nixexprs.tar.zst";
  };

  outputs = inputs: {
    devShells = builtins.mapAttrs (system: pkgs: {
      default = pkgs.mkShell {
        packages = with pkgs;[
          ruff
          kicad
          prek
          (python3.withPackages (ps: [ps.ipython ps.skidl]))
        ];
        env = {
          KICAD_SYMBOL_DIR = "${pkgs.kicad.libraries.symbols}/share/kicad/symbols";
          KICAD10_SYMBOL_DIR = "${pkgs.kicad.libraries.symbols}/share/kicad/symbols";
        };
      };
    }) inputs.nixpkgs.legacyPackages;
  };
}

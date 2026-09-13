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
          (python3.withPackages (ps: [ps.ipython]))
        ];
      };
    }) inputs.nixpkgs.legacyPackages;
  };
}

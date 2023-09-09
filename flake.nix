{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-23.05";
    # unstable-nixpkgs.url = "github:NixOS/nixpkgs/unstable";
    systems.url = "github:nix-systems/default";
    devenv.url = "github:cachix/devenv";
  };

  nixConfig = {
    extra-trusted-public-keys = "devenv.cachix.org-1:w1cLUi8dv3hnoSPGAuibQv+f9TZLr6cv/Hm9XgU50cw=";
    extra-substituters = "https://devenv.cachix.org";
  };

  outputs = { self,nixpkgs, devenv, systems, ... } @ inputs:
    let
      forEachSystem = nixpkgs.lib.genAttrs (import systems);
    in
    {
      devShells = forEachSystem
        (system:
          let
            pkgs = nixpkgs.legacyPackages.${system};
            # unstable-pkgs = unstable-nixpkgs.legacyPackages.${system};
          in
          {
            default = devenv.lib.mkShell {
              inherit inputs pkgs;
              modules = [
                {
                  # https://devenv.sh/reference/options/
                packages = with pkgs; [
                python3.pkgs.flake8
                python3.pkgs.black
                ];

              dotenv.disableHint = true;
              languages.python.enable = true;
              languages.python.venv.enable = true;
              env.LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
              "${pkgs.stdenv.cc.cc.lib}"
              "${pkgs.zlib}"

              ];
                }
              ];
            };
          });
    };
}

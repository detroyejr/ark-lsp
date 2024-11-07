let
  pkgs = import <nixpkgs> { };
  pname = "ark-posit";
  version = "0.5.1";
  rev = "b8505c504eb10be0e9cb948e1631f151825facdb";
  ark-posit = pkgs.rustPlatform.buildRustPackage {
    inherit pname version;
    src = pkgs.fetchFromGitHub {
      inherit rev;
      owner = "posit-dev";
      repo = "ark";
      hash = "sha256-+0+UFiJsQKFT/DLeu3LF8RFik7Iqv873gzu+RP83GiA=";
    };
    cargoLock = {
      lockFile = builtins.fetchurl {
        url = "https://raw.githubusercontent.com/posit-dev/ark/${rev}/Cargo.lock";
        sha256 = "sha256:1v5klikaib1cf6d9qggqa3cch4jscl5ixibi1bbfa9bhcky86fjh";
      };
      outputHashes = {
        "dap-0.4.1-alpha1" = "sha256-nUsTazH1riI0nglWroDKDWoHEEtNEtpwn6jCH2N7Ass=";
        "tree-sitter-r-1.1.0" = "sha256-a7vgmOY9K8w8vwMlOLBmUnXpWpVP+YlOilGODaI07y4=";
      };
    };
    buildInputs = [
      pkgs.libcxx
      pkgs.libgcc
      pkgs.rustPlatform.bindgenHook
    ];
    doCheck = false;
  };
  # utils.so needs to be patched for this to work with nix.
  R-patch = pkgs.R.overrideAttrs (oldAttrs: {
    postFixup = ''
      echo ${pkgs.which} > $out/nix-support/undetected-runtime-dependencies
      find $out -name "*.so" -exec patchelf {} --add-rpath $out/lib/R/lib \;
    '';
  });
in
pkgs.mkShell {
  packages = [
    R-patch
    ark-posit
    pkgs.python3Packages.jupyter-console
  ];
}

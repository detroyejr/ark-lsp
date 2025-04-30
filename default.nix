let
  pkgs = import <nixpkgs> { };
  version = "0.5.1";
  pname = "ark";
  ark-posit = pkgs.rustPlatform.buildRustPackage {

      inherit pname version;
      src = pkgs.fetchFromGitHub {
        owner = "posit-dev";
        repo = pname;
        tag = version;
        hash = "sha256-ajGquqGKs002mJihnHoaMW+qkc4zgqGRnMT4b2BT2cU=";
      };

      useFetchCargoVendor = true;
      cargoHash = "sha256-xPIPEugJKS7nGcc+kKRCmNptTgcd6yK8sqBFO/Hpj0U=";

      doCheck = false;

      buildInputs = [
        pkgs.libcxx
        pkgs.libgcc
      ];

      nativeBuildInputs = [
        pkgs.autoPatchelfHook
        pkgs.rustPlatform.bindgenHook
      ];
    };
in
pkgs.mkShell {
  packages = [
    ark-posit
    pkgs.python3Packages.jupyter-console
  ];
}

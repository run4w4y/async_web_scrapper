with import <nixpkgs> {};
with pkgs.python3Packages;

buildPythonPackage rec {
  name = "async_web_scrapper";
  src = ./.;
  propagatedBuildInputs = [ httpx idna beautifulsoup4 trio ];
}
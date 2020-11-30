{ pkgs ? import <nixos-unstable> {}, ...  }:

pkgs.mkShell {
  name = "async-web-scrapper";
  
  buildInputs = with pkgs; [
    (python38.withPackages (p: with p; [
      httpx
      beautifulsoup4
      aiofiles
    ]))
  ];

  shellHook = ''
    export TERM=xterm-256color
  '';
}
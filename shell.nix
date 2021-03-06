{ pkgs ? import <nixos-unstable> {}, ...  }:

pkgs.mkShell {
  name = "async-web-scrapper";
  
  buildInputs = with pkgs; [
    (python38.withPackages (p: with p; [
      httpx
      idna
      beautifulsoup4
      trio
    ]))
  ];

  shellHook = ''
    export TERM=xterm-256color
  '';
}
"""Comprueba los archivos y anclas de la portada empaquetada para Pages."""

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class Portada(HTMLParser):
    def __init__(self):
        super().__init__()
        self.anclas = set()
        self.enlaces = set()

    def handle_starttag(self, tag, attrs):
        atributos = dict(attrs)
        if "id" in atributos:
            ancla = atributos["id"]
            if ancla in self.anclas:
                raise ValueError(f"Ancla duplicada: {ancla}")
            self.anclas.add(ancla)
        self.enlaces.update(atributos[key] for key in ("href", "src") if key in atributos)


def verificar(carpeta: Path) -> None:
    portada = Portada()
    portada.feed((carpeta / "index.html").read_text(encoding="utf-8"))
    errores = []
    for enlace in sorted(portada.enlaces):
        url = urlsplit(enlace)
        if url.scheme or url.netloc:
            continue
        if url.path and not (carpeta / unquote(url.path)).is_file():
            errores.append(f"Falta el archivo: {enlace}")
        if not url.path and url.fragment and url.fragment not in portada.anclas:
            errores.append(f"Falta el destino: {enlace}")
    if errores:
        raise SystemExit("\n".join(errores))
    print("Archivos y anclas de la portada verificados.")


if __name__ == "__main__":
    verificar(Path(sys.argv[1]))

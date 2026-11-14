"""Monta la web en la carpeta _site antes de cifrarla.

- Copia las páginas (portada, sesiones/ y releases/) y la carpeta assets/.
- Inserta los datos (sesiones, releases, valoraciones del grupo y observatorio) dentro de
  cada página que los usa, para que queden cifrados junto con la página y no se publiquen sueltos.
Lo ejecuta GitHub Actions (.github/workflows/update.yml).
"""
import json
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"
PAGES = ["index.html", "sesiones/index.html", "releases/index.html", "actualidad/index.html"]
DATA = {
    "/*__SESSIONS__*/null": "sessions.json",
    "/*__RELEASES__*/null": "releases.json",
    "/*__RELNOTES__*/null": "releases_notas.json",
    "/*__ACTUALIDAD__*/null": "actualidad.json",
}


def load(name: str) -> str:
    path = ROOT / "data" / name
    if not path.exists():
        return "null"
    data = json.loads(path.read_text(encoding="utf-8"))
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def main() -> None:
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir()
    shutil.copytree(ROOT / "assets", SITE / "assets")
    inline = {marker: load(name) for marker, name in DATA.items()}
    for page in PAGES:
        src = (ROOT / page).read_text(encoding="utf-8")
        for marker, value in inline.items():
            src = src.replace(marker, value, 1)
        out = SITE / page
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(src, encoding="utf-8")
    print("Web montada en _site: " + ", ".join(PAGES))


if __name__ == "__main__":
    main()

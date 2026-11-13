"""Monta la web en la carpeta _site antes de cifrarla.

- Copia las páginas (index.html y sesiones/) y la carpeta assets/.
- Inserta las sesiones (data/sessions.json) y el observatorio (data/observatorio.json)
  dentro de cada página, para que
  los datos queden cifrados junto con la página y no se publiquen sueltos.
Lo ejecuta GitHub Actions (.github/workflows/update.yml).
"""
import json
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"
PAGES = ["index.html", "sesiones/index.html"]
PLACEHOLDER = "/*__SESSIONS__*/null"
OBS_PLACEHOLDER = "/*__OBSERVATORIO__*/null"


def main() -> None:
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir()
    shutil.copytree(ROOT / "assets", SITE / "assets")

    data = json.loads((ROOT / "data" / "sessions.json").read_text(encoding="utf-8"))
    inline = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    obs_path = ROOT / "data" / "observatorio.json"
    obs = json.loads(obs_path.read_text(encoding="utf-8")) if obs_path.exists() else {"items": []}
    obs_inline = json.dumps(obs, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    for page in PAGES:
        src = (ROOT / page).read_text(encoding="utf-8")
        if PLACEHOLDER not in src:
            raise SystemExit(f"ERROR: falta el marcador de datos en {page}")
        out = SITE / page
        out.parent.mkdir(parents=True, exist_ok=True)
        src = src.replace(PLACEHOLDER, inline, 1).replace(OBS_PLACEHOLDER, obs_inline, 1)
        out.write_text(src, encoding="utf-8")
    print(f"Web montada en _site con {len(data.get('events', []))} sesiones.")


if __name__ == "__main__":
    main()

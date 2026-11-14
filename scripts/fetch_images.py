#!/usr/bin/env python3
"""Busca la imagen oficial (og:image) de cada noticia de data/actualidad.json.

Solo consulta fuentes oficiales (braze.com y salesforce.com) para no usar fotos de
medios con derechos. Si una noticia ya tiene imagen, o su fuente no es oficial, no la
toca: la web mostrará una ilustración de marca. Nunca rompe nada: si algo falla, sigue.
"""
import json, re, sys, urllib.request
from pathlib import Path
from urllib.parse import urlparse, urljoin

FILE = Path(__file__).resolve().parent.parent / "data" / "actualidad.json"
OFFICIAL = ("braze.com", "salesforce.com")
OG = [re.compile(p, re.I | re.S) for p in (
    r'<meta[^>]+property=["\']og:image(?::secure_url)?["\'][^>]+content=["\']([^"\']+)',
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
    r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)',
)]


def official(url):
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in OFFICIAL)


def og_image(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (COE Braze Iberia hub; +https://github.com)",
        "Accept": "text/html"})
    with urllib.request.urlopen(req, timeout=20) as r:
        page = r.read(600_000).decode("utf-8", "replace")
    for rx in OG:
        m = rx.search(page)
        if m:
            img = urljoin(url, m.group(1).replace("&amp;", "&").strip())
            # La imagen genérica de Braze no aporta: mejor la ilustración de marca
            if img.startswith("https://") and "default-opengraph" not in img:
                return img
    return ""


def main():
    data = json.loads(FILE.read_text(encoding="utf-8"))
    items = list(data.get("noticias", [])) + list((data.get("salesforce") or {}).get("items", []))
    changed = 0
    for it in items:
        url = it.get("url") or ""
        if it.get("image") or it.get("sin_imagen") or not url or not official(url):
            continue
        try:
            img = og_image(url)
        except Exception as e:  # noqa: BLE001
            print(f"  sin imagen ({e.__class__.__name__}): {url}")
            continue
        if img:
            it["image"] = img
            print(f"  imagen: {url}")
        else:
            it["sin_imagen"] = True   # no volver a buscarla cada día
            print(f"  sin imagen propia: {url}")
        changed += 1
    if changed:
        FILE.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Noticias revisadas: {changed}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"Aviso: no se pudieron revisar las imágenes ({e})")
        sys.exit(0)

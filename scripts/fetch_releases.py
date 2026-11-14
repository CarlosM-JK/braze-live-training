"""Descarga las release notes de Braze (2026 en adelante) y las guarda en data/releases.json.

Fuente: https://www.braze.com/docs/releases/history y la página de cada release.
- El texto de cada funcionalidad sale del Markdown que Braze incrusta en la página
  (botón "Copy for LLM", atributo data-markdown-content).
- La etiqueta de disponibilidad (General availability / Beta / Early access) sale del HTML,
  donde aparece justo debajo del título de cada funcionalidad.

Lo ejecuta GitHub Actions (.github/workflows/update.yml). Si algo falla, termina con error
y NO sobrescribe el archivo, así la web sigue mostrando los últimos datos buenos.
"""
import datetime as dt
import html
import json
import pathlib
import re
import sys
import time
import urllib.request

BASE = "https://www.braze.com"
HISTORY = BASE + "/docs/releases/history"
MIN_YEAR = 2026
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "releases.json"
UA = {"User-Agent": "Mozilla/5.0 (COE Braze Iberia hub; GitHub Actions)"}

LINK_RE = re.compile(r"/docs/releases/(\d{4})/(\d{1,2})_(\d{1,2})_(\d{2})/")
MD_RE = re.compile(r"data-markdown-content=([\"'])(.*?)\1", re.S)
H3_RE = re.compile(
    r"<h3[^>]*\bid=[\"']([^\"']+)[\"'][^>]*>(.*?)</h3>\s*"
    r"(?:<p>\s*<span[^>]*>\s*([^<]+?)\s*</span>)?",
    re.S,
)
LABELS = {"general availability": "ga", "beta": "beta", "early access": "early"}
MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")


def get(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


def clean(text: str) -> str:
    text = re.sub(r"<sup>\s*TM\s*</sup>", "", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", html.unescape(text))
    return re.sub(r"\s+", " ", text).strip()


def summarize(lines):
    """Primer párrafo en texto plano (con la lista que lo sigue si termina en ':'), máx. ~420 caracteres."""
    blocks, cur = [], []
    for ln in lines:
        if ln.strip():
            cur.append(ln.strip())
        elif cur:
            blocks.append(cur)
            cur = []
    if cur:
        blocks.append(cur)
    if not blocks:
        return ""
    picked = blocks[0]
    if picked and picked[-1].endswith(":") and len(blocks) > 1:
        picked = picked + blocks[1]
    parts = []
    for ln in picked:
        ln = re.sub(r"^[*-]\s+", "", ln)
        parts.append(ln)
    text = " ".join(parts)
    text = MD_LINK.sub(r"\1", text)
    text = re.sub(r"\*\*|__|`", "", text)
    text = re.sub(r"(?<!\w)\*(?!\s)|(?<!\s)\*(?!\w)", "", text)
    text = clean(text)
    if len(text) > 420:
        text = text[:420].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    return text


def first_doc_link(lines):
    for ln in lines:
        for _, url in MD_LINK.findall(ln):
            if "braze.com/docs" in url:
                return url
    return ""


def parse_release(page: str, url: str):
    m = MD_RE.search(page)
    if not m:
        raise ValueError(f"sin Markdown incrustado en {url}")
    md = html.unescape(m.group(2))

    items, section, cur = [], "", None
    for ln in md.splitlines():
        if ln.startswith("### "):
            cur = {"title": clean(ln[4:]), "section": section, "lines": []}
            items.append(cur)
        elif ln.startswith("## "):
            section = clean(ln[3:])
            cur = None
        elif ln.startswith("# "):
            continue
        elif cur is not None:
            cur["lines"].append(ln)

    heads = [(hid, clean(t), (lab or "").strip()) for hid, t, lab in H3_RE.findall(page)]
    if len(heads) != len(items):
        raise ValueError(f"{url}: {len(items)} funcionalidades en Markdown y {len(heads)} en HTML")

    out = []
    for it, (hid, htitle, lab) in zip(items, heads):
        out.append({
            "id": hid,
            "title": it["title"] or htitle,
            "section": it["section"],
            "label": LABELS.get(lab.lower(), ""),
            "summary": summarize(it["lines"]),
            "doc": first_doc_link(it["lines"]),
        })
    return out


def main() -> int:
    try:
        hist = get(HISTORY)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR al descargar el historial: {exc}", file=sys.stderr)
        return 1

    found = {}
    for m in LINK_RE.finditer(hist):
        year, mo, day, yy = (int(x) for x in m.groups())
        if year >= MIN_YEAR:
            found[m.group(0)] = dt.date(year, mo, day)
    if not found:
        print("ERROR: no se han encontrado releases en el historial.", file=sys.stderr)
        return 1

    releases = []
    for path, date in sorted(found.items(), key=lambda kv: kv[1], reverse=True):
        url = BASE + path
        try:
            items = parse_release(get(url), url)
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR en {url}: {exc}", file=sys.stderr)
            return 1
        releases.append({"date": date.isoformat(), "url": url, "items": items})
        time.sleep(1)

    total = sum(len(r["items"]) for r in releases)
    if OUT.exists():
        try:
            if json.loads(OUT.read_text(encoding="utf-8")).get("releases") == releases:
                print(f"Sin cambios ({len(releases)} releases, {total} funcionalidades).")
                return 0
        except json.JSONDecodeError:
            pass

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "source": HISTORY,
        "releases": releases,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Actualizado: {len(releases)} releases, {total} funcionalidades.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

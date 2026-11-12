"""Descarga las sesiones en directo de Braze Learning y las guarda en data/sessions.json.

Lo ejecuta GitHub Actions cada día (.github/workflows/update.yml).
Si la descarga falla o no devuelve sesiones, el script termina con error y NO
sobrescribe el archivo, así la página sigue mostrando los últimos datos buenos.
"""
import datetime as dt
import json
import pathlib
import sys
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

TZ = "Europe/Madrid"
SOURCE = "https://learning.braze.com/calendar"
ENDPOINT = "https://learning.braze.com/get_calendar_events"
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "sessions.json"


def main() -> int:
    now = dt.datetime.now(ZoneInfo(TZ))
    params = {
        "start": (now - dt.timedelta(days=7)).strftime("%Y-%m-%d"),
        "end": (now + dt.timedelta(days=365)).strftime("%Y-%m-%d"),
        "timezone": TZ,
    }
    url = f"{ENDPOINT}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (braze-live-training calendar; GitHub Actions)",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = json.load(resp)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR al descargar {url}: {exc}", file=sys.stderr)
        return 1

    if not isinstance(raw, list) or not raw:
        print("ERROR: la respuesta no contiene sesiones; no se actualiza el archivo.", file=sys.stderr)
        return 1

    events = []
    for ev in raw:
        if not ev.get("title") or not ev.get("start"):
            continue
        events.append({
            "title": ev["title"],
            "start": ev["start"],
            "end": ev.get("end") or ev["start"],
            "url": ev.get("url", ""),
            "tags": ev.get("tags") or [],
        })
    events.sort(key=lambda e: e["start"])

    # Solo reescribe si cambian las sesiones (evita commits diarios sin cambios).
    if OUT.exists():
        try:
            old = json.loads(OUT.read_text(encoding="utf-8"))
            if old.get("events") == events:
                print(f"Sin cambios ({len(events)} sesiones).")
                return 0
        except json.JSONDecodeError:
            pass

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "updated": now.isoformat(timespec="seconds"),
        "source": SOURCE,
        "timezone": TZ,
        "count": len(events),
        "events": events,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Actualizado: {len(events)} sesiones.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

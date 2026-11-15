#!/usr/bin/env python3
"""Genera el pódcast de la última release de Braze con NotebookLM.

1. Busca en data/releases.json las releases (desde PRIMERA) sin pódcast, de la más reciente a la más antigua.
2. Monta la ficha en Markdown (data/podcasts/ficha-AAAA-MM-DD.md) con sus novedades,
   las valoraciones del grupo (data/releases_notas.json) y el contexto del COE.
3. Con notebooklm-py (librería NO oficial): crea un cuaderno, sube la ficha, genera el
   resumen de audio con scripts/podcast_instrucciones.txt y descarga el audio a
   assets/podcasts/release-AAAA-MM-DD.m4a.
4. Lo apunta en data/podcasts.json, que la web lee para mostrar el reproductor.

Si algo falla, termina sin romper la web (la release se queda sin audio y se reintenta
al día siguiente). Con --solo-ficha genera la ficha sin llamar a NotebookLM.
"""
import json, re, subprocess, sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RELEASES = ROOT / "data" / "releases.json"
NOTAS = ROOT / "data" / "releases_notas.json"
INDEX = ROOT / "data" / "podcasts.json"
FICHAS = ROOT / "data" / "podcasts"
AUDIO = ROOT / "assets" / "podcasts"
PROMPT = ROOT / "scripts" / "podcast_instrucciones.txt"

PRIMERA = "2026-08-20"      # no se generan pódcasts de releases anteriores
IDIOMA = "es"               # NotebookLM solo ofrece es / es_419 / es_MX
FORMATO = "deep-dive"       # "Información detallada"
DURACION = "default"
LABEL = {"ga": "GA", "beta": "Beta", "early": "Early access"}
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


def load(p, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def fecha_larga(iso):
    d = date.fromisoformat(iso)
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def ficha(rel, notas):
    """Ficha en Markdown para NotebookLM. Solo datos de la release y del grupo."""
    items = rel["items"]
    sdk = [i for i in items if re.match(r"sdk", i["section"], re.I)]
    resto = [i for i in items if i not in sdk]
    secciones = []
    for it in resto:
        if it["section"] not in secciones:
            secciones.append(it["section"])
    n_ga = sum(1 for i in items if i.get("label") == "ga")
    out = [
        f"# Release de Braze del {fecha_larga(rel['date'])}: ficha para el pódcast del COE Braze Iberia",
        "",
        f"> Fuente: release notes oficiales de Braze, {rel['url']}",
        "> Audiencia: consultores de Marketing Automation de Jakala que trabajan con Braze en proyectos de cliente.",
        "> Disponibilidad tal como la publica Braze: GA (disponible para todos), Beta, Early access (hay que pedirla a Braze). "
        "Si una novedad no indica etiqueta, no la menciones como GA.",
        "> Las valoraciones del grupo (casos de uso, si la tenemos, responsable) solo existen donde se indican expresamente.",
        "",
        f"La release incluye {len(items)} novedades, {n_ga} de ellas en GA, repartidas en: {', '.join(secciones)}.",
        "Interesan especialmente las novedades de Shopify, de IA (BrazeAI) y de datos, "
        "y todo lo relacionado con clientes alojados en Europa (clúster EU).",
        "",
    ]
    for sec in secciones:
        out += [f"## {sec}", ""]
        for it in (i for i in resto if i["section"] == sec):
            lab = LABEL.get(it.get("label") or "", "sin etiqueta")
            out += [f"### {it['title']} ({lab})", "", it.get("summary") or "", ""]
            n = (notas.get("items") or {}).get(f"{rel['date']}#{it['id']}")
            if n:
                extra = []
                if n.get("casos_uso"): extra.append(f"Casos de uso según el grupo: {n['casos_uso']}")
                if n.get("en_instancia") in ("si", "sí", True): extra.append("La tenemos activa.")
                if n.get("pedir") in ("si", "sí", True): extra.append("El grupo propone pedirla a Braze.")
                if n.get("responsable"): extra.append(f"Responsable de su explotación: {n['responsable']}.")
                if n.get("comentario"): extra.append(f"Comentario: {n['comentario']}")
                if extra:
                    out += ["Valoración del COE: " + " ".join(extra), ""]
    if sdk:
        out += ["## SDK (solo para equipos técnicos)", "",
                "Hay actualizaciones de SDK. Basta con mencionarlas y recomendar revisar los changelogs "
                "antes de actualizar las apps de los clientes: " + "; ".join(i["title"] for i in sdk) + ".", ""]
    return "\n".join(out).strip() + "\n"


def nlm(*args, timeout=1500):
    """Ejecuta el CLI de notebooklm y devuelve su JSON."""
    r = subprocess.run(["notebooklm", *args, "--json"], capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"notebooklm {' '.join(args[:2])}: {(r.stderr or r.stdout).strip()[-400:]}")
    try:
        return json.loads(r.stdout)
    except ValueError:
        return {"raw": r.stdout}


def find_id(obj, keys=("id", "notebook_id", "source_id", "artifact_id", "task_id")):
    """Busca el primer identificador en una respuesta JSON del CLI."""
    if isinstance(obj, dict):
        for k in keys:
            if isinstance(obj.get(k), str) and obj[k]:
                return obj[k]
        for v in obj.values():
            found = find_id(v, keys)
            if found:
                return found
    if isinstance(obj, list):
        for v in obj:
            found = find_id(v, keys)
            if found:
                return found
    return None


def main():
    solo_ficha = "--solo-ficha" in sys.argv
    rels = load(RELEASES, {}).get("releases", [])
    index = load(INDEX, {"_ayuda": "Pódcasts de releases generados con NotebookLM. Lo mantiene scripts/podcast_release.py.", "podcasts": {}})
    pend = [r for r in rels if r["date"] >= PRIMERA and r["date"] not in index["podcasts"]]
    if not pend:
        print("Todas las releases tienen pódcast.")
        return
    notas = load(NOTAS, {})
    hechas = 0
    for rel in sorted(pend, key=lambda r: r["date"], reverse=True):
        try:
            if generar(rel, notas, index, solo_ficha):
                hechas += 1
        except Exception as e:  # noqa: BLE001
            # Lo más probable es el límite diario de NotebookLM: el resto se hace mañana
            print(f"Aviso: pódcast de {rel['date']} pendiente ({e}).")
            if not hechas:
                raise
            break
    print(f"Pódcasts generados en esta ejecución: {hechas}")


def generar(rel, notas, index, solo_ficha):
    FICHAS.mkdir(parents=True, exist_ok=True)
    fpath = FICHAS / f"ficha-{rel['date']}.md"
    fpath.write_text(ficha(rel, notas), encoding="utf-8")
    print(f"Ficha: {fpath.relative_to(ROOT)}")
    if solo_ficha:
        return False

    nb = find_id(nlm("create", f"Braze release {rel['date']} · COE Braze Iberia"))
    src = find_id(nlm("source", "add", str(fpath), "--type", "file", "--title", f"Release {rel['date']}", "-n", nb), ("source_id", "id"))
    nlm("source", "wait", src, "-n", nb, "--timeout", "300")
    try:  # segunda fuente: la página oficial con el texto completo (opcional)
        url_src = find_id(nlm("source", "add", rel["url"], "--type", "url", "-n", nb), ("source_id", "id"))
        nlm("source", "wait", url_src, "-n", nb, "--timeout", "300")
    except Exception as e:  # noqa: BLE001
        print(f"  (sin la página oficial como fuente: {e})")
    gen = nlm("generate", "audio", "--prompt-file", str(PROMPT), "-n", nb,
              "--format", FORMATO, "--length", DURACION, "--language", IDIOMA, "--retry", "2")
    art = find_id(gen, ("artifact_id", "task_id", "id"))
    nlm("artifact", "wait", art, "-n", nb, "--timeout", "1800", timeout=2000)
    AUDIO.mkdir(parents=True, exist_ok=True)
    apath = AUDIO / f"release-{rel['date']}.m4a"
    nlm("download", "audio", str(apath), "-a", art, "-n", nb, "--force")
    if not apath.exists() or apath.stat().st_size < 50_000:
        raise RuntimeError("El audio descargado no existe o está vacío.")
    index["podcasts"][rel["date"]] = {
        "audio": f"assets/podcasts/{apath.name}",
        "ficha": f"data/podcasts/{fpath.name}",
        "generado": date.today().isoformat(),
        "notebook": nb,
    }
    INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Pódcast listo: {apath.relative_to(ROOT)} ({apath.stat().st_size // 1024} KB)")
    return True


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"Aviso: no se pudo generar el pódcast ({e}). Se reintentará en la próxima ejecución.")
        sys.exit(1)

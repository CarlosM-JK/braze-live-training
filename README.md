# COE Braze Iberia · Hub

Web interna del grupo de referentes de Braze (Jakala), protegida con contraseña.

- **Portada** (`index.html`): presentación del hub con Chroco, próximas sesiones en horario ES, releases (próximamente) y observatorio.
- **Sesiones** (`sesiones/index.html`): calendario de las sesiones en directo de [Braze Learning](https://learning.braze.com/calendar) en hora de Madrid.
- **Releases** (`releases/index.html`): lanzamientos de Braze desde 2026 en una cronología con índice por meses; cada lanzamiento se despliega y muestra sus novedades en pestañas por sección, con la valoración del grupo. La portada muestra los cuatro últimos.

## Cómo funciona

| Archivo | Qué hace |
|---|---|
| `index.html`, `sesiones/index.html` | Las páginas (diseño y textos en ES/EN/FR/IT). |
| `assets/` | Logos de Jakala y las tres poses de Chroco. |
| `data/sessions.json` | Sesiones de Braze Learning. Lo actualiza el robot. |
| `data/releases.json` | Release notes de Braze desde 2026. Lo actualiza el robot. |
| `data/releases_notas.json` | Valoración del grupo por funcionalidad (casos de uso, si la tenemos, si pedirla, responsable). Se edita a mano. |
| `data/observatorio.json` | Noticias del observatorio Braze + Salesforce (estado: anunciado / rumoreado / disponible, en ES/EN/FR/IT). De momento se edita a mano. |
| `scripts/fetch_sessions.py` | Descarga las sesiones del calendario público de Braze Learning. |
| `scripts/fetch_releases.py` | Lee braze.com/docs/releases/history y cada release de 2026 en adelante. |
| `scripts/build_site.py` | Monta la web e inserta las sesiones dentro de las páginas. |
| `scripts/staticrypt_template.html` | Pantalla de contraseña con la imagen de Jakala. |
| `.github/workflows/update.yml` | El robot: descarga, monta, cifra y publica. |

El robot se ejecuta cada día y cada vez que se sube un cambio a `main`:
1. Descarga las sesiones y las release notes de Braze (si algo falla, publica igualmente con los últimos datos buenos y avisa).
2. Monta la web e inserta los datos dentro de las páginas.
3. Cifra cada página con la contraseña del grupo (StatiCrypt). Sin contraseña, el contenido es ilegible.
4. Publica el resultado en GitHub Pages.

## Contraseña

- Se guarda como secreto del repositorio: **Settings → Secrets and variables → Actions → `STATICRYPT_PASSWORD`**. No es visible para nadie, tampoco en el repositorio público.
- Para cambiarla: edita el secreto y lanza el robot (**Actions → Actualizar y publicar la web → Run workflow**). Quien tuviera marcado "Recordarme" tendrá que volver a introducirla.
- Una sola contraseña para todo el hub; "Recordarme" la guarda 30 días en ese navegador.

## Importante

- **Este repositorio es público.** Las páginas publicadas están cifradas, pero los archivos del repositorio se pueden leer. No subas aquí información interna, de clientes ni contraseñas: eso va en SharePoint.
- El calendario de Braze no tiene una API documentada; si Braze cambia su web, el robot avisará con un error en Actions.
- GitHub desactiva las tareas programadas tras 60 días sin actividad: se reactivan en Actions → Enable workflow.

## Añadir una noticia al observatorio

Edita `data/observatorio.json` (lápiz en GitHub) y añade un elemento a `items`, con `status` (`anunciado`, `rumoreado` o `disponible`), `date` (AAAA-MM-DD), `source`, `url` (opcional), `image` (opcional, ruta a una imagen propia en `assets/`) y `title` / `text` en `es`, `en`, `fr` e `it`. Al guardar, la web se republica sola. Con más de una noticia, el carrusel se activa automáticamente.

## Destacados de la portada

Por defecto, la portada muestra dos novedades de cada lanzamiento elegidas automáticamente (las primeras en GA de las secciones con más peso, sin SDK ni Partnerships). Para fijarlas a mano, añade en `data/releases_notas.json` dentro de `destacados` la fecha y los ids:

```json
"destacados": { "2026-11-12": ["account-objects", "send-to-destination"] }
```

## Valorar una release

Cada funcionalidad de la página de releases muestra "Pendiente de valorar por el grupo" hasta que se añade su valoración en `data/releases_notas.json`. La clave es la fecha de la release + `#` + el id de la funcionalidad (el id es lo que aparece tras `#` en el enlace "Ver en Braze Docs" de la ficha). Ejemplo:

```json
"items": {
  "2026-11-12#segment-reporting": {
    "casos_uso": "Medir el rendimiento de segmentos clave a lo largo del tiempo para clientes retail.",
    "en_instancia": "por_confirmar",
    "pedir": "si",
    "responsable": "Nombre",
    "comentario": "Revisar con el equipo de producto."
  }
}
```

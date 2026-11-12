# Braze Live Training · Calendario del grupo

Calendario de las sesiones en directo de [Braze Learning](https://learning.braze.com/calendar), en hora de Madrid, con filtros por área temática, tipo de sesión, idioma y horario laboral en España.

Uso interno del COE Braze Iberia (Jakala). Solo contiene información pública publicada por Braze.

## Cómo funciona

| Archivo | Qué hace |
|---|---|
| `index.html` | La página. Lee las sesiones de `data/sessions.json`. |
| `data/sessions.json` | Las sesiones. Lo actualiza el robot; no hace falta editarlo a mano. |
| `scripts/fetch_sessions.py` | Descarga las sesiones del calendario público de Braze Learning. |
| `.github/workflows/update.yml` | El robot: ejecuta el script cada día y guarda los cambios. |

Cada día, GitHub Actions descarga el calendario de los próximos 12 meses. Si hay cambios, actualiza `data/sessions.json` y GitHub Pages publica la página con los datos nuevos. Si la descarga falla, no se toca nada y la página sigue mostrando los últimos datos buenos.

## Tareas habituales

- **Forzar una actualización:** pestaña **Actions** → *Actualizar sesiones de Braze* → **Run workflow**.
- **Comprobar que el robot funciona:** pestaña **Actions**; cada ejecución aparece en verde (bien) o en rojo (error).
- **Cambiar la clasificación por áreas:** función `areaOf` en `index.html` (palabras clave del título).
- **Cambiar el horario ES:** en `index.html`, `mins>=510 && mins<=1200` (de 8:30 a 20:00, en minutos desde medianoche).

## Notas

- El calendario de Braze no tiene una API documentada. Si Braze cambia su web, el robot fallará (aparecerá en rojo en Actions) y habrá que revisar `scripts/fetch_sessions.py`.
- La página está marcada para que los buscadores no la indexen, pero cualquiera con el enlace puede verla.

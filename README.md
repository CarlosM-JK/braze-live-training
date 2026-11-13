# COE Braze Iberia · Hub

Web interna del grupo de referentes de Braze (Jakala), protegida con contraseña.

- **Portada** (`index.html`): presentación del hub con Chroco, próximas sesiones en horario ES, releases (próximamente) y observatorio.
- **Sesiones** (`sesiones/index.html`): calendario de las sesiones en directo de [Braze Learning](https://learning.braze.com/calendar) en hora de Madrid.
- Próximamente: Releases de Braze, biblioteca de casos de uso y observatorio Braze + Salesforce.

## Cómo funciona

| Archivo | Qué hace |
|---|---|
| `index.html`, `sesiones/index.html` | Las páginas (diseño y textos en ES/EN/FR/IT). |
| `assets/` | Logos de Jakala y las tres poses de Chroco. |
| `data/sessions.json` | Sesiones de Braze Learning. Lo actualiza el robot. |
| `data/observatorio.json` | Noticias del observatorio Braze + Salesforce (estado: anunciado / rumoreado / disponible, en ES/EN/FR/IT). De momento se edita a mano. |
| `scripts/fetch_sessions.py` | Descarga las sesiones del calendario público de Braze Learning. |
| `scripts/build_site.py` | Monta la web e inserta las sesiones dentro de las páginas. |
| `scripts/staticrypt_template.html` | Pantalla de contraseña con la imagen de Jakala. |
| `.github/workflows/update.yml` | El robot: descarga, monta, cifra y publica. |

El robot se ejecuta cada día y cada vez que se sube un cambio a `main`:
1. Descarga las sesiones de Braze (si falla, publica igualmente con los últimos datos y avisa).
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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_autotext.py — Compilador, Sincronizador de Producción (web/) y Generador de Portal (index.html)
para el proyecto AutoText v12 (100% Offline + GitHub Pages Ready).
"""

import argparse
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
WEB_DIR = ROOT / "web"
BASE_EDITOR = ROOT / "Autotext_Final.html"
BASE_WEB = WEB_DIR / "Autotext_Final.html"

# Diccionario clínico oftalmológico estándar (valores fisiológicos por defecto)
STANDARD_OPHTHALMO_VARS = {
    "nombre_paciente": {"label": "Nombre del Paciente", "type": "text", "defaultValue": ""},
    "documento_paciente": {"label": "Documento / HC", "type": "text", "defaultValue": ""},
    "edad_paciente": {"label": "Edad", "type": "number", "defaultValue": ""},
    "fecha_consulta": {"label": "Fecha", "type": "date", "defaultValue": ""},
    "medico_tratante": {"label": "Médico Tratante", "type": "text", "defaultValue": "Dr. José Luis Navia"},
    "ojo_a_operar": {
        "label": "Ojo a Intervenir",
        "type": "select",
        "options": ["Ojo Derecho (OD)", "Ojo Izquierdo (OI)", "Ambos Ojos (AO)"],
        "defaultValue": "Ojo Derecho (OD)",
    },
    "procedimiento": {
        "label": "Procedimiento Quirúrgico",
        "type": "text",
        "defaultValue": "Facoemulsificación + Implante de Lente Intraocular Plegable",
    },
    "tipo_anestesia": {
        "label": "Tipo de Anestesia",
        "type": "select",
        "options": ["Tópica + Intracameral", "Peribulbar", "Subtenoniana", "General"],
        "defaultValue": "Tópica + Intracameral",
    },
    "od_av_sc_lejos": {"label": "AV SC Lejos OD", "type": "text", "defaultValue": "20/20"},
    "oi_av_sc_lejos": {"label": "AV SC Lejos OI", "type": "text", "defaultValue": "20/20"},
    "od_av_cc_lejos": {"label": "AV CC Lejos OD", "type": "text", "defaultValue": "20/20"},
    "oi_av_cc_lejos": {"label": "AV CC Lejos OI", "type": "text", "defaultValue": "20/20"},
    "od_cornea": {"label": "Córnea OD", "type": "text", "defaultValue": "Transparente, sin lesiones epiteliales"},
    "oi_cornea": {"label": "Córnea OI", "type": "text", "defaultValue": "Transparente, sin lesiones epiteliales"},
    "od_cristalino": {"label": "Cristalino OD", "type": "text", "defaultValue": "Transparente"},
    "oi_cristalino": {"label": "Cristalino OI", "type": "text", "defaultValue": "Transparente"},
    "od_pio": {"label": "PIO OD (mmHg)", "type": "number", "defaultValue": "14"},
    "oi_pio": {"label": "PIO OI (mmHg)", "type": "number", "defaultValue": "14"},
    "od_retina": {"label": "Retina / Fondo OD", "type": "text", "defaultValue": "Aplicada, mácula y papila de aspecto normal"},
    "oi_retina": {"label": "Retina / Fondo OI", "type": "text", "defaultValue": "Aplicada, mácula y papila de aspecto normal"},
    "diagnostico_principal": {"label": "Diagnóstico Principal", "type": "text", "defaultValue": ""},
    "plan_tratamiento": {"label": "Plan y Conducta", "type": "textarea", "defaultValue": ""},
}


def extract_template_metadata(html_path: Path) -> dict:
    content = html_path.read_text(encoding="utf-8")
    title_match = re.search(r'id="template-title"[^>]*value="([^"]*)"', content)
    if not title_match:
        title_match = re.search(r"<title>(.*?)</title>", content)
    title = title_match.group(1).strip() if title_match else html_path.stem.replace("_", " ")

    vars_match = re.search(
        r'<script id="variables-data" type="application/json">\s*(.*?)\s*</script>',
        content,
        re.DOTALL,
    )
    variables = []
    if vars_match:
        try:
            variables = json.loads(vars_match.group(1).strip() or "[]")
        except Exception:
            variables = []

    text_match = re.search(
        r'<script id="template-text-data" type="text/plain">(.*?)</script>',
        content,
        re.DOTALL,
    )
    template_text = text_match.group(1).strip("\r\n") if text_match else ""

    return {
        "filename": html_path.name,
        "stem": html_path.stem,
        "title": title,
        "variables": variables,
        "template_text": template_text,
    }


def inject_into_html(base_html: str, title: str, variables: list, template_text: str, is_editor: bool) -> str:
    out = re.sub(r"<title>.*?</title>", f"<title>Plantilla: {html.escape(title)}</title>", base_html, count=1)
    out = re.sub(
        r'(id="template-title"[^>]*value=")[^"]*(")',
        rf"\g<1>{html.escape(title)}\2",
        out,
        count=1,
    )
    vars_json = json.dumps(variables, ensure_ascii=False, indent=2)
    out = re.sub(
        r'(<script id="variables-data" type="application/json">)\s*.*?\s*(</script>)',
        lambda m: f"{m.group(1)}\n{vars_json}\n    {m.group(2)}",
        out,
        count=1,
        flags=re.DOTALL,
    )
    out = re.sub(
        r'(<script id="template-text-data" type="text/plain">).*?(</script>)',
        lambda m: f"{m.group(1)}\n{template_text}\n{m.group(2)}",
        out,
        count=1,
        flags=re.DOTALL,
    )
    if is_editor:
        out = re.sub(
            r'(<textarea id="template-text"[^>]*>).*?(</textarea>)',
            lambda m: f"{m.group(1)}{html.escape(template_text)}{m.group(2)}",
            out,
            count=1,
            flags=re.DOTALL,
        )
    return out


def sync_web_directory() -> list:
    WEB_DIR.mkdir(exist_ok=True)
    base_web_html = BASE_WEB.read_text(encoding="utf-8")
    templates_info = []

    for html_file in sorted(ROOT.glob("*.html")):
        if html_file.name.lower() == "index.html":
            continue
        meta = extract_template_metadata(html_file)
        templates_info.append(meta)

        if html_file.name == "Autotext_Final.html":
            continue

        web_target = WEB_DIR / html_file.name
        rendered_web = inject_into_html(
            base_web_html,
            meta["title"],
            meta["variables"],
            meta["template_text"],
            is_editor=False,
        )
        web_target.write_text(rendered_web, encoding="utf-8")
        print(f"[SYNC] web/{html_file.name} sincronizado ({len(meta['variables'])} variables)")

    return templates_info


def classify_template(stem: str) -> str:
    s = stem.upper()
    if "CIRUGIA" in s or "PREQUIRURGICO" in s:
        return "Quirúrgico"
    if "CATARATA" in s:
        return "Catarata / Faco"
    if "FORMULA" in s or "RECOMENDACIONES" in s:
        return "Fórmulas y Postoperatorio"
    if "AUTOTEXT_FINAL" in s:
        return "Lienzo Base"
    return "Consulta General"


def generate_portal_index(templates_info: list) -> Path:
    cards_data = []
    for t in templates_info:
        if t["filename"] == "Autotext_Final.html":
            continue
        preview = re.sub(r"\s+", " ", t["template_text"])[:160]
        cards_data.append({
            "filename": t["filename"],
            "title": t["title"],
            "category": classify_template(t["stem"]),
            "varCount": len(t["variables"]),
            "preview": preview + ("..." if len(t["template_text"]) > 160 else ""),
            "webUrl": f"web/{t['filename']}",
            "editorUrl": t["filename"],
        })

    cards_json = json.dumps(cards_data, ensure_ascii=False, indent=2)
    today = date.today().isoformat()

    index_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AutoText v12 — Portal Clínico & Quirúrgico</title>
<style>
  :root {{
    --bg: #f8fafc;
    --card: #ffffff;
    --text: #0f172a;
    --muted: #64748b;
    --primary: #4f46e5;
    --primary-hover: #4338ca;
    --border: #e2e8f0;
    --badge-bg: #eef2ff;
    --badge-txt: #4338ca;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #0f172a;
      --card: #1e293b;
      --text: #f8fafc;
      --muted: #94a3b8;
      --primary: #6366f1;
      --primary-hover: #818cf8;
      --border: #334155;
      --badge-bg: rgba(99, 102, 241, 0.18);
      --badge-txt: #a5b4fc;
    }}
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
    padding: 1.5rem;
  }}
  .wrap {{ max-width: 1280px; margin: 0 auto; }}
  header {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
    margin-bottom: 1.25rem;
  }}
  .brand h1 {{ font-size: 1.35rem; font-weight: 800; }}
  .brand p {{ font-size: 0.85rem; color: var(--muted); }}
  .toolbar {{
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
    margin-bottom: 1.25rem;
  }}
  .search-input {{
    flex: 1;
    min-width: 260px;
    padding: 0.65rem 1rem;
    border-radius: 10px;
    border: 1px solid var(--border);
    background: var(--card);
    color: var(--text);
    font-size: 0.92rem;
  }}
  .filter-btn {{
    padding: 0.55rem 0.95rem;
    border-radius: 10px;
    border: 1px solid var(--border);
    background: var(--card);
    color: var(--muted);
    cursor: pointer;
    font-weight: 600;
    font-size: 0.84rem;
  }}
  .filter-btn.active, .filter-btn:hover {{
    background: var(--primary);
    color: #fff;
    border-color: var(--primary);
  }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 1.1rem;
  }}
  .card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.15rem;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 0.85rem;
    transition: transform 0.15s, border-color 0.15s;
  }}
  .card:hover {{ border-color: var(--primary); transform: translateY(-2px); }}
  .badge {{
    display: inline-block;
    background: var(--badge-bg);
    color: var(--badge-txt);
    font-size: 0.74rem;
    font-weight: 700;
    padding: 0.2rem 0.6rem;
    border-radius: 999px;
  }}
  .card h2 {{ font-size: 1.05rem; margin-top: 0.35rem; }}
  .preview {{
    font-size: 0.8rem;
    color: var(--muted);
    background: var(--bg);
    padding: 0.6rem;
    border-radius: 8px;
    border: 1px solid var(--border);
    min-height: 60px;
  }}
  .actions {{ display: flex; gap: 0.5rem; }}
  .btn {{
    flex: 1;
    text-align: center;
    text-decoration: none;
    padding: 0.55rem 0.75rem;
    border-radius: 8px;
    font-size: 0.82rem;
    font-weight: 700;
    border: 1px solid var(--border);
    color: var(--text);
  }}
  .btn-primary {{
    background: var(--primary);
    color: #fff;
    border-color: var(--primary);
  }}
  .btn-primary:hover {{ background: var(--primary-hover); }}
  footer {{
    margin-top: 2rem;
    text-align: center;
    font-size: 0.8rem;
    color: var(--muted);
  }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="brand">
      <h1>🩺 AutoText v12 — Portal de Plantillas Clínicas</h1>
      <p>100% Offline & GitHub Pages Ready · Actualizado: {today}</p>
    </div>
    <div style="display:flex; gap:0.6rem;">
      <a class="btn btn-primary" href="Autotext_Final.html" style="flex:initial; padding:0.6rem 1.1rem;">➕ Crear Nueva Plantilla (Lienzo)</a>
    </div>
  </header>

  <div class="toolbar">
    <input type="text" id="q" class="search-input" placeholder="🔍 Buscar plantilla por nombre, categoría o contenido..." oninput="render()">
    <button class="filter-btn active" onclick="setCat('ALL', this)">Todas ({len(cards_data)})</button>
    <button class="filter-btn" onclick="setCat('Consulta General', this)">Consulta</button>
    <button class="filter-btn" onclick="setCat('Catarata / Faco', this)">Catarata</button>
    <button class="filter-btn" onclick="setCat('Quirúrgico', this)">Quirúrgico</button>
    <button class="filter-btn" onclick="setCat('Fórmulas y Postoperatorio', this)">Fórmulas / Postop</button>
  </div>

  <div id="grid" class="grid"></div>

  <footer>
    AutoText v12 · Motor HTML Autocontenido con Impresión Membretada · Sincronizado con NAS-760025 y GitHub Pages
  </footer>
</div>

<script id="catalog-data" type="application/json">
{cards_json}
</script>
<script>
  const items = JSON.parse(document.getElementById('catalog-data').textContent);
  let activeCat = 'ALL';

  function setCat(cat, btn) {{
    activeCat = cat;
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    render();
  }}

  function render() {{
    const q = (document.getElementById('q').value || '').toLowerCase();
    const grid = document.getElementById('grid');
    grid.innerHTML = '';
    items.filter(it => {{
      const matchCat = activeCat === 'ALL' || it.category === activeCat;
      const matchQ = it.title.toLowerCase().includes(q) ||
                     it.filename.toLowerCase().includes(q) ||
                     it.preview.toLowerCase().includes(q);
      return matchCat && matchQ;
    }}).forEach(it => {{
      const card = document.createElement('div');
      card.className = 'card';
      card.innerHTML = `
        <div>
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span class="badge">${{it.category}}</span>
            <span style="font-size:0.75rem; color:var(--muted); font-weight:600;">⚙️ ${{it.varCount}} variables</span>
          </div>
          <h2>${{it.title}}</h2>
          <div style="font-size:0.74rem; color:var(--muted); margin-bottom:0.5rem;">📄 ${{it.filename}}</div>
          <div class="preview">${{it.preview}}</div>
        </div>
        <div class="actions">
          <a class="btn btn-primary" href="${{it.webUrl}}">🌐 Modo Consulta (Limpio)</a>
          <a class="btn" href="${{it.editorUrl}}">✏️ Modo Editor</a>
        </div>
      `;
      grid.appendChild(card);
    }});
  }}
  render();
</script>
</body>
</html>
"""
    index_path = ROOT / "index.html"
    index_path.write_text(index_html, encoding="utf-8")
    print(f"[PORTAL] index.html generado con {len(cards_data)} plantillas activas.")
    return index_path


def build_from_txt(txt_path: Path, output_name: str = "") -> None:
    if not txt_path.exists():
        raise FileNotFoundError(f"No existe el borrador: {txt_path}")
    raw_text = txt_path.read_text(encoding="utf-8").strip()
    found_ids = []
    for m in re.finditer(r"\{\{([a-zA-Z0-9_]+)\}\}", raw_text):
        vid = m.group(1).lower()
        if vid not in found_ids:
            found_ids.append(vid)

    variables = []
    for vid in found_ids:
        if vid in STANDARD_OPHTHALMO_VARS:
            spec = STANDARD_OPHTHALMO_VARS[vid]
            variables.append({
                "id": vid,
                "label": spec["label"],
                "type": spec["type"],
                "options": spec.get("options", []),
                "defaultValue": spec.get("defaultValue", ""),
            })
        else:
            label = vid.replace("_", " ").title().replace("Od", "OD").replace("Oi", "OI")
            variables.append({
                "id": vid,
                "label": label,
                "type": "text",
                "options": [],
                "defaultValue": "",
            })

    stem = Path(output_name).stem if output_name else txt_path.stem
    title = stem.replace("_", " ").title()
    editor_out = ROOT / f"{stem}.html"
    web_out = WEB_DIR / f"{stem}.html"

    editor_html = inject_into_html(
        BASE_EDITOR.read_text(encoding="utf-8"),
        title,
        variables,
        raw_text,
        is_editor=True,
    )
    web_html = inject_into_html(
        BASE_WEB.read_text(encoding="utf-8"),
        title,
        variables,
        raw_text,
        is_editor=False,
    )
    editor_out.write_text(editor_html, encoding="utf-8")
    web_out.write_text(web_html, encoding="utf-8")
    print(f"[BUILD] Plantilla creada: {editor_out.name} + web/{web_out.name} ({len(variables)} variables)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Automatizador de AutoText v12 (Sync web/ + Portal index.html + Compilador .txt)")
    parser.add_argument("--from-txt", metavar="ARCHIVO_TXT", help="Compila un archivo .txt con {{variables}} a HTML (raíz y web/)")
    parser.add_argument("--output", default="", help="Nombre de salida opcional para --from-txt")
    args = parser.parse_args()

    if args.from_txt:
        build_from_txt(Path(args.from_txt), args.output)

    templates_info = sync_web_directory()
    generate_portal_index(templates_info)
    return 0


if __name__ == "__main__":
    sys.exit(main())

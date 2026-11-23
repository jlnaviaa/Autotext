#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_autotext.py — Compilador, Normalizador Clínico, Sincronizador (raíz + web/)
y Generador de Portal (index.html) para AutoText v12 (100% Offline + GitHub Pages Ready).
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


def derive_web_base_from_editor(relative_portal: str = "../index.html") -> str:
    """Deriva la vista clínica de 2 columnas (Variables Izquierda | Texto Editado Derecha) sin edición de plantilla."""
    WEB_DIR.mkdir(exist_ok=True)
    editor_html = BASE_EDITOR.read_text(encoding="utf-8")
    # Limpiar posible bloque previo de presets-catalog-data
    editor_html = re.sub(
        r'\s*<script id="presets-catalog-data" type="application/json">.*?</script>',
        "",
        editor_html,
        flags=re.DOTALL,
    )

    web_html = editor_html.replace(
        "grid-template-columns: 350px 1.2fr 1fr;",
        "grid-template-columns: 1.2fr 1fr;",
    )
    web_html = web_html.replace('href="index.html"', f'href="{relative_portal}"')
    web_html = re.sub(
        r'(<input\s+type="text"\s+id="template-title"\s+class="template-title-input")(?![^>]*readonly)',
        r'\1 readonly',
        web_html,
        count=1,
    )
    web_html = re.sub(
        r'\s*<button id="save-app-btn"[^>]*>.*?</button>',
        "",
        web_html,
        flags=re.DOTALL,
    )
    web_html = re.sub(
        r'<!-- COLUMNA 1: CONFIGURACIÓN.*?<!-- COLUMNA 2: FORMULARIO',
        "<!-- COLUMNA 2: FORMULARIO",
        web_html,
        flags=re.DOTALL,
    )
    if relative_portal == "../index.html":
        BASE_WEB.write_text(web_html, encoding="utf-8")
        print("[BASE] web/Autotext_Final.html actualizado (2 columnas sin edición de plantilla).")
    return web_html


def get_variable_eye_side(v: dict) -> str:
    """Clasifica una variable en 'od' (mitad izquierda), 'oi' (mitad derecha) o 'both' (ancho completo)."""
    if not v or v.get("type") == "textarea":
        return "both"
    vid = str(v.get("id", ""))
    label = str(v.get("label", ""))
    od_re = re.compile(r"(^|[\s_\-\(\/])(od|ojo\s+derecho)($|[\s_\-\)\/\.,:])", re.IGNORECASE)
    oi_re = re.compile(r"(^|[\s_\-\(\/])(oi|ojo\s+izquierdo)($|[\s_\-\)\/\.,:])", re.IGNORECASE)

    is_od = bool(re.search(r"(^od_|_od$)", vid, re.IGNORECASE) or od_re.search(vid) or od_re.search(label))
    is_oi = bool(re.search(r"(^oi_|_oi$)", vid, re.IGNORECASE) or oi_re.search(vid) or oi_re.search(label))

    if is_od and not is_oi:
        return "od"
    if is_oi and not is_od:
        return "oi"
    return "both"


def get_eye_base_key(v: dict) -> str:
    vid = str(v.get("id", "")).lower()
    vid = re.sub(r"(^od_|^oi_|_od$|_oi$)", "", vid)
    vid = re.sub(r"(^|_)(od|oi)(_|$)", "_", vid)
    return vid.strip("_")


def pair_and_interleave_od_oi_variables(variables: list) -> list:
    """
    Intercala pares [OD, OI] dentro de cada bloque consecutivo de variables de ojo
    para que Ojo Derecho ocupe siempre la mitad izquierda y Ojo Izquierdo la mitad derecha
    en la misma fila, manteniendo las variables de ambos ojos ('both') a ancho completo.
    """
    result = []
    od_bucket = []
    oi_bucket = []

    def flush_buckets():
        nonlocal od_bucket, oi_bucket
        if not od_bucket and not oi_bucket:
            return
        used_oi = set()
        for idx, od_var in enumerate(od_bucket):
            result.append(od_var)
            base_key = get_eye_base_key(od_var)
            match_idx = -1
            for j, oi_var in enumerate(oi_bucket):
                if j not in used_oi and get_eye_base_key(oi_var) == base_key:
                    match_idx = j
                    break
            if match_idx == -1 and idx < len(oi_bucket) and idx not in used_oi:
                match_idx = idx
            if match_idx != -1:
                used_oi.add(match_idx)
                result.append(oi_bucket[match_idx])
        for j, oi_var in enumerate(oi_bucket):
            if j not in used_oi:
                result.append(oi_var)
        od_bucket = []
        oi_bucket = []

    for v in variables:
        side = get_variable_eye_side(v)
        if side == "od":
            od_bucket.append(v)
        elif side == "oi":
            oi_bucket.append(v)
        else:
            flush_buckets()
            result.append(v)
    flush_buckets()
    return result


def normalize_template_data(stem: str, title: str, variables: list, template_text: str) -> tuple[str, list, str]:
    """Limpia erratas clínicas, elimina Markdown residual, corrige defaults y deduplica bloques."""
    # 1. Títulos descriptivos
    title_overrides = {
        "RECOMENDACIONES_CATARATA": "Recomendaciones Postoperatorias de Catarata",
        "CIRUGIA": "Descripción Quirúrgica y Fórmula de Facoemulsificación",
        "Descripcion_Recomendaciones_Formula": "Descripción Quirúrgica, Recomendaciones y Fórmula Tórica",
    }
    if stem in title_overrides:
        title = title_overrides[stem]

    # 2. Deduplicar bloque repetido en Descripcion_Recomendaciones_Formula
    if stem == "Descripcion_Recomendaciones_Formula":
        dup_marker = "Facoemulsificación de cristalino con implante de lente intraocular ojo izquierdo"
        if dup_marker in template_text:
            template_text = template_text.split(dup_marker)[0].rstrip()

        # Reemplazar Lugar:/Fecha:/Hora: vacíos por variables con valor por defecto
        template_text = re.sub(
            r"Lugar:\s*\r?\nFecha:\s*\r?\nHora:\s*",
            "Lugar: {{ubicacion_control}}\nFecha: {{fecha_control}}\nHora: {{hora_control}}\n",
            template_text,
        )

    # 3. Unir numeración suelta "1.\nTexto" -> "1. Texto" para texto plano limpio e impresión
    template_text = re.sub(r"(?m)^(\d+)\.\s*\r?\n+\s*", r"\1. ", template_text)

    # 4. Limpiar sintaxis Markdown residual en plantillas de historia clínica
    clean_lines = []
    for line in template_text.splitlines():
        s = line.strip()
        if re.match(r"^-{3,}$", s):
            continue
        # Quitar encabezados markdown ## o ###
        line = re.sub(r"^\s*#{1,6}\s+", "", line)
        # Convertir viñetas markdown "*   **Texto**:" o "*   Texto" a texto clínico plano
        if re.match(r"^\s*\*\s+", line):
            indent = len(line) - len(line.lstrip())
            body = re.sub(r"^\s*\*\s+", "", line).replace("**", "")
            if indent >= 4:
                line = f"  {body}"
            elif ":" in body and len(body) < 65:
                line = body
            else:
                line = f"- {body}"
        clean_lines.append(line.rstrip())

    template_text = "\n".join(clean_lines)
    template_text = re.sub(r"\n{3,}", "\n\n", template_text).strip()

    # 5. Correcciones ortográficas y clínicas
    replacements = {
        "N0CP0": "N0C0P0",
        "retina adiherida": "retina adherida",
        "Pueden ocurri en cirugías": "Pueden ocurrir en cirugías",
        "enfermos morales": "enfermos mentales",
        "el dia de la cirugía": "el día de la cirugía",
        "comuniquese": "comuníquese",
        "( OFTAMOX )": "(OFTAMOX)",
        "( CORTIOFTAL )": "(CORTIOFTAL)",
        "( NEPAOFTAL )": "(NEPAOFTAL)",
        "Unidad Quirúrgica Calida) .": "Unidad Quirúrgica Calida).",
    }
    for bad, good in replacements.items():
        template_text = template_text.replace(bad, good)

    # 6. Normalizar variables y valores por defecto
    existing_ids = {v.get("id") for v in variables}
    for v in variables:
        vid = v.get("id", "")
        val = v.get("defaultValue", "")
        if isinstance(val, str) and "N0CP0" in val:
            v["defaultValue"] = val.replace("N0CP0", "N0C0P0")

        if stem == "Prequirurgico" and vid == "camara_anterior":
            v["options"] = ["IV", "III", "II", "I"]
            v["defaultValue"] = "IV"

        if stem == "RECOMENDACIONES_CATARATA":
            if vid == "ojo_intervenido":
                v["defaultValue"] = "ojo derecho"
            elif vid == "fecha_control":
                v["type"] = "text"
                v["defaultValue"] = "en 24 a 48 horas"
            elif vid == "hora_control":
                v["defaultValue"] = "por confirmar"
            elif vid == "ubicacion_control":
                v["defaultValue"] = "Edificio de Colores consultorio 1122 en Cali"

        if stem == "Descripcion_Recomendaciones_Formula":
            defaults_map = {
                "ojo_intervenido": "ojo derecho",
                "lente": "plegable una sola pieza",
                "principal": "2.5",
                "principal_eje": "100",
                "relajante": "1.0",
                "relajante_eje": "10",
                "poder_lente": "21.0",
                "poder_cilindro": "0.0",
                "eje_lente": "0",
                "Hallazgos": "Sin hallazgos relevantes",
                "Complicaciones": "Sin complicaciones",
            }
            if vid in defaults_map and not v.get("defaultValue"):
                v["defaultValue"] = defaults_map[vid]

        # Garantizar que cualquier select tenga un defaultValue válido de su lista de opciones
        if v.get("type") == "select":
            opts = v.get("options") or []
            if opts and v.get("defaultValue") not in opts:
                v["defaultValue"] = opts[0]

    if stem == "Descripcion_Recomendaciones_Formula":
        extra_vars = [
            {
                "id": "ubicacion_control",
                "label": "Lugar del control",
                "type": "select",
                "options": [
                    "Edificio de Colores consultorio 1122 en Cali",
                    "Clínica Nuestra Señora del Palmar consultorio 104 en Palmira",
                ],
                "defaultValue": "Edificio de Colores consultorio 1122 en Cali",
            },
            {
                "id": "fecha_control",
                "label": "Fecha del control",
                "type": "text",
                "options": [],
                "defaultValue": "en 24 a 48 horas",
            },
            {
                "id": "hora_control",
                "label": "Hora del control",
                "type": "text",
                "options": [],
                "defaultValue": "por confirmar",
            },
        ]
        for ev in extra_vars:
            if ev["id"] not in existing_ids:
                variables.append(ev)

    # 7. Emparejar e intercalar bloques OD (mitad izquierda) y OI (mitad derecha),
    # manteniendo variables de ambos ojos (ej. mov_ext) a ancho completo.
    variables = pair_and_interleave_od_oi_variables(variables)

    return title, variables, template_text


def extract_template_metadata(html_path: Path) -> dict:
    content = html_path.read_text(encoding="utf-8")
    title_match = re.search(r'id="template-title"[^>]*value="([^"]*)"', content)
    if not title_match:
        title_match = re.search(r"<title>(.*?)</title>", content)
    title = title_match.group(1).strip() if title_match else html_path.stem.replace("_", " ")
    title = re.sub(r"^Plantilla:\s*", "", title).strip()

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

    title, variables, template_text = normalize_template_data(
        html_path.stem, title, variables, template_text
    )

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


def sync_all_templates() -> list:
    base_web_html = derive_web_base_from_editor(relative_portal="../index.html")
    base_root_2col_html = derive_web_base_from_editor(relative_portal="index.html")
    templates_info = []
    presets_for_editor = []

    for html_file in sorted(ROOT.glob("*.html")):
        if html_file.name.lower() == "index.html":
            continue
        meta = extract_template_metadata(html_file)
        templates_info.append(meta)

        if html_file.name == "Autotext_Final.html":
            continue

        presets_for_editor.append({
            "filename": meta["filename"],
            "title": meta["title"],
            "variables": meta["variables"],
            "template_text": meta["template_text"],
        })

        # Actualizar plantilla en raíz a 2 columnas (la edición de plantilla es sólo en Autotext_Final.html)
        rendered_root = inject_into_html(
            base_root_2col_html,
            meta["title"],
            meta["variables"],
            meta["template_text"],
            is_editor=False,
        )
        html_file.write_text(rendered_root, encoding="utf-8")

        # Actualizar plantilla en web/ (2 columnas: Variables Izquierda | Texto Editado Derecha)
        web_target = WEB_DIR / html_file.name
        rendered_web = inject_into_html(
            base_web_html,
            meta["title"],
            meta["variables"],
            meta["template_text"],
            is_editor=False,
        )
        web_target.write_text(rendered_web, encoding="utf-8")
        print(f"[SYNC] {html_file.name} + web/{html_file.name} sincronizados a 2 columnas ({len(meta['variables'])} variables)")

    # Inyectar el catálogo de plantillas dentro de Autotext_Final.html (único editor de plantillas)
    editor_raw = BASE_EDITOR.read_text(encoding="utf-8")
    editor_raw = re.sub(
        r'\s*<script id="presets-catalog-data" type="application/json">.*?</script>',
        "",
        editor_raw,
        flags=re.DOTALL,
    )
    presets_json = json.dumps(presets_for_editor, ensure_ascii=False, indent=2)
    preset_script_tag = f'\n    <!-- CATÁLOGO DE PLANTILLAS PARA EDICIÓN EN AUTOTEXT -->\n    <script id="presets-catalog-data" type="application/json">\n{presets_json}\n    </script>\n'
    editor_raw = editor_raw.replace(
        "<!-- DATOS DE LAS VARIABLES INYECTADOS -->",
        f"{preset_script_tag}    <!-- DATOS DE LAS VARIABLES INYECTADOS -->",
        1,
    )
    BASE_EDITOR.write_text(editor_raw, encoding="utf-8")
    print(f"[EDITOR] Autotext_Final.html actualizado con selector de edición para {len(presets_for_editor)} plantillas.")

    return templates_info


def classify_template(stem: str) -> str:
    s = stem.upper()
    if "CONSENTIMIENTO" in s:
        return "Consentimientos"
    if "NEONATO" in s or "LACTANTE" in s or "PEDIATRICO" in s or "NINO" in s:
        return "Pediátrico / Neonato"
    if "CIRUGIA" in s or "PREQUIRURGICO" in s:
        return "Quirúrgico"
    if "CATARATA" in s and "RECOMENDACIONES" not in s and "POSTOPERATORIO" not in s:
        return "Catarata / Faco"
    if "FORMULA" in s or "RECOMENDACIONES" in s or "POSTOPERATORIO" in s:
        return "Fórmulas y Postoperatorio"
    if "AUTOTEXT_FINAL" in s:
        return "Lienzo Base"
    return "Consulta General"


def classify_workflow_badge(stem: str) -> str:
    s = stem.upper()
    if "FORMULA" in s or "RECOMENDACIONES" in s or "CIRUGIA" in s:
        return "📋 HC + 🖨️ Impresión Verum"
    return "📋 Historia Clínica + 🖨️ Verum"


def generate_portal_index(templates_info: list) -> Path:
    cards_data = []
    for t in templates_info:
        if t["filename"] == "Autotext_Final.html":
            continue
        preview = re.sub(r"\s+", " ", t["template_text"])[:165]
        cards_data.append({
            "filename": t["filename"],
            "title": t["title"],
            "category": classify_template(t["stem"]),
            "workflow": classify_workflow_badge(t["stem"]),
            "varCount": len(t["variables"]),
            "preview": preview + ("..." if len(t["template_text"]) > 165 else ""),
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
    --kbd-bg: #f1f5f9;
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
      --kbd-bg: #334155;
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
    margin-bottom: 0.9rem;
  }}
  .brand h1 {{ font-size: 1.35rem; font-weight: 800; }}
  .brand p {{ font-size: 0.85rem; color: var(--muted); }}
  .shortcuts-bar {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.6rem 1rem;
    margin-bottom: 1.1rem;
    font-size: 0.8rem;
    color: var(--muted);
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    align-items: center;
  }}
  kbd {{
    background: var(--kbd-bg);
    border: 1px solid var(--border);
    border-radius: 5px;
    padding: 0.1rem 0.4rem;
    font-family: monospace;
    font-size: 0.76rem;
    color: var(--text);
    font-weight: 700;
  }}
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
      <h1>🩺 AutoText v12 — Portal de Plantillas Clínicas y Quirúrgicas</h1>
      <p>Dr. José Luis Navia Ávila · Texto Plano para Historia Clínica + Impresión con Marca de Agua Verum · Actualizado: {today}</p>
    </div>
    <div style="display:flex; gap:0.6rem;">
      <a class="btn btn-primary" href="Autotext_Final.html" style="flex:initial; padding:0.6rem 1.1rem;">✏️ Editor de Plantillas (AutoText)</a>
    </div>
  </header>

  <div class="shortcuts-bar">
    <span>⚡ <strong>Atajos rápidos dentro de cada plantilla:</strong></span>
    <span><kbd>Alt+C</kbd> Copiar minúscula</span>
    <span><kbd>Alt+M</kbd> Copiar MAYÚSCULA</span>
    <span><kbd>Alt+P</kbd> Imprimir Documento</span>
    <span><kbd>Alt+R</kbd> Botón Restablecer</span>
    <span><kbd>Alt+L</kbd> 📲 Enlace Híbrido (Móvil → Portátil/PC)</span>
    <span><kbd>Ctrl+S</kbd> Guardar (sólo en Editor AutoText)</span>
  </div>

  <div class="toolbar">
    <input type="text" id="q" class="search-input" placeholder="🔍 Buscar plantilla por nombre, categoría o contenido clínico..." oninput="render()">
    <button class="filter-btn active" onclick="setCat('ALL', this)">Todas ({len(cards_data)})</button>
    <button class="filter-btn" onclick="setCat('Consulta General', this)">Consulta</button>
    <button class="filter-btn" onclick="setCat('Pediátrico / Neonato', this)">👶 Pediátrico / Neonato</button>
    <button class="filter-btn" onclick="setCat('Catarata / Faco', this)">Catarata</button>
    <button class="filter-btn" onclick="setCat('Quirúrgico', this)">Quirúrgico</button>
    <button class="filter-btn" onclick="setCat('Consentimientos', this)">✍️ Consentimientos</button>
    <button class="filter-btn" onclick="setCat('Fórmulas y Postoperatorio', this)">Fórmulas / Postop</button>
  </div>

  <div id="grid" class="grid"></div>

  <footer>
    AutoText v12 · 100% Offline & Autocontenido · Impresión Membretada Verum · Sincronizado con NAS-760025 y GitHub Pages
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
          <div style="display:flex; justify-content:space-between; align-items:center; gap:0.4rem; flex-wrap:wrap;">
            <span class="badge">${{it.category}}</span>
            <span style="font-size:0.73rem; color:var(--muted); font-weight:600;">${{it.workflow}} · ⚙️ ${{it.varCount}} vars</span>
          </div>
          <h2>${{it.title}}</h2>
          <div style="font-size:0.74rem; color:var(--muted); margin-bottom:0.5rem;">📄 ${{it.filename}}</div>
          <div class="preview">${{it.preview}}</div>
        </div>
        <div class="actions">
          <a class="btn btn-primary" href="${{it.webUrl}}">🌐 Abrir Plantilla (2 Columnas)</a>
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
        vid = m.group(1)
        if vid not in found_ids:
            found_ids.append(vid)

    variables = []
    for vid in found_ids:
        low_id = vid.lower()
        if low_id in STANDARD_OPHTHALMO_VARS:
            spec = STANDARD_OPHTHALMO_VARS[low_id]
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
    title, variables, raw_text = normalize_template_data(stem, title, variables, raw_text)
    editor_out = ROOT / f"{stem}.html"
    web_out = WEB_DIR / f"{stem}.html"

    base_web_html = derive_web_base_from_editor(relative_portal="../index.html")
    base_root_2col_html = derive_web_base_from_editor(relative_portal="index.html")
    editor_html = inject_into_html(
        base_root_2col_html,
        title,
        variables,
        raw_text,
        is_editor=False,
    )
    web_html = inject_into_html(
        base_web_html,
        title,
        variables,
        raw_text,
        is_editor=False,
    )
    editor_out.write_text(editor_html, encoding="utf-8")
    web_out.write_text(web_html, encoding="utf-8")
    print(f"[BUILD] Plantilla creada: {editor_out.name} + web/{web_out.name} ({len(variables)} variables)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Automatizador de AutoText v12 (Sync raíz/web/ + Portal index.html + Compilador .txt)")
    parser.add_argument("--from-txt", metavar="ARCHIVO_TXT", help="Compila un archivo .txt con {{variables}} a HTML (raíz y web/)")
    parser.add_argument("--output", default="", help="Nombre de salida opcional para --from-txt")
    args = parser.parse_args()

    if args.from_txt:
        build_from_txt(Path(args.from_txt), args.output)

    templates_info = sync_all_templates()
    generate_portal_index(templates_info)
    return 0


if __name__ == "__main__":
    sys.exit(main())

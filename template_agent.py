#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
template_agent.py - Agente interactivo "template-agent" para AutoText v12.

Fijo: idioma es | ejecucion local (LEGION/Ollama o heuristica 0 tokens) | export html (+ json).
Flujo:
  1. IMPORT  : URL, archivo (.txt/.md/.html) o texto pegado (--text / stdin '-').
  2. ANALIZA : detecta variables candidatas (diccionario global + heuristica + SLM opcional).
  3. ELIGE   : lista numerada; el usuario escoge cuales usar (CLI interactivo o WebUI en 2 pasos).
  4. EXPORTA : web/<STEM>.html, web/<STEM>.json (solo variables usadas) y
               web/variables_globales.json (diccionario comun a todas las plantillas).
  5. PUSH    : NO se hace aqui. Usar la skill `checkpoint` (GitHub Pages).

Modos:
  CLI interactivo : python template_agent.py --import <URL|archivo|-> [--name STEM]
  WebUI/OpenClaw  : 1) --analyze  --import <fuente>   -> imprime lista + SESSION_ID
                    2) --select <SESSION_ID> "1,3,5-7|all" --name STEM [--edit "3 id=x label=Y"]
"""

import argparse
import html as htmllib
import json
import os
import re
import shlex
import sys
import unicodedata
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path

import build_autotext as B

ROOT = Path(__file__).parent
WEB_DIR = ROOT / "web"
DRAFTS_DIR = ROOT / "borradores_sites"
MEM_DIR = ROOT / "training_memory"
SESSIONS_DIR = MEM_DIR / "agent_sessions"
PICKS_LOG = MEM_DIR / "template_agent_picks.jsonl"
GLOBAL_DICT_PATH = WEB_DIR / "variables_globales.json"
DEFAULT_OLLAMA = os.environ.get("OLLAMA_URL", "http://192.168.0.212:11434")

VALID_TYPES = {"text", "textarea", "number", "date", "select"}

PII_LABEL_RE = re.compile(
    r"paciente|nombre|documento|c[eé]dula|identificaci|tel[eé]fono|celular|direcci[oó]n|"
    r"correo|e-?mail|nacimiento|historia cl|\bhc\b|\bcc\b",
    re.I,
)
PII_VALUE_PATTERNS = [
    ("documento", re.compile(r"\b\d{6,}\b")),
    ("email", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("telefono", re.compile(r"\+?\d[\d\s-]{8,}\d")),
    ("fecha", re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b")),
]


# ----------------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------------

def slug(text: str) -> str:
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()
    t = re.sub(r"[^a-z0-9]+", "_", t).strip("_")
    return t or "variable"


def norm_label(text: str) -> str:
    return slug(text)


def html_to_text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style|noscript).*?</\1>", " ", raw)
    raw = re.sub(r"(?i)<br\s*/?>|</(p|div|li|tr|h[1-6]|section|article)>", "\n", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    raw = htmllib.unescape(raw)
    lines = [re.sub(r"[ \t\u00a0]+", " ", ln).strip() for ln in raw.splitlines()]
    out, blank = [], 0
    for ln in lines:
        if ln:
            out.append(ln)
            blank = 0
        else:
            blank += 1
            if blank == 1 and out:
                out.append("")
    return "\n".join(out).strip()


def import_source(source: str | None, text: str | None) -> tuple[str, str]:
    """Devuelve (texto_plano, etiqueta_fuente)."""
    if text:
        return text.strip(), "texto pegado"
    if not source:
        raise SystemExit("Falta fuente: use --import <URL|archivo|-> o --text.")
    if source == "-":
        return sys.stdin.read().strip(), "stdin"
    if re.match(r"^https?://", source, re.I):
        req = urllib.request.Request(source, headers={"User-Agent": "template-agent/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            raw = resp.read().decode(charset, errors="replace")
        return html_to_text(raw), source
    p = Path(source)
    if not p.exists():
        raise SystemExit(f"No existe la fuente: {source}")
    raw = p.read_text(encoding="utf-8", errors="replace")
    if p.suffix.lower() in (".html", ".htm"):
        raw = html_to_text(raw)
    return raw.strip(), str(p)


# ----------------------------------------------------------------------------
# Diccionario global
# ----------------------------------------------------------------------------

def load_global() -> dict:
    if GLOBAL_DICT_PATH.exists():
        try:
            data = json.loads(GLOBAL_DICT_PATH.read_text(encoding="utf-8"))
            return data.get("variables", data) if isinstance(data, dict) else {}
        except Exception:
            pass
    return {k: dict(v) for k, v in B.STANDARD_OPHTHALMO_VARS.items()}


def save_global(variables: dict) -> None:
    WEB_DIR.mkdir(exist_ok=True)
    payload = {
        "_meta": {
            "description": "Variables comunes a todas las plantillas AutoText (es). Cada plantilla usa solo las que necesita.",
            "lang": "es",
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        },
        "variables": dict(sorted(variables.items())),
    }
    GLOBAL_DICT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def global_lookup(gdict: dict) -> dict:
    """label normalizado / id -> id global."""
    idx = {}
    for vid, spec in gdict.items():
        idx[vid.lower()] = vid
        idx[norm_label(spec.get("label", vid))] = vid
    return idx


# ----------------------------------------------------------------------------
# Deteccion de candidatos
# ----------------------------------------------------------------------------

def guess_type(value: str) -> str:
    v = value.strip()
    if re.fullmatch(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", v):
        return "date"
    if re.fullmatch(r"-?\d+([.,]\d+)?", v):
        return "number"
    if len(v) > 120:
        return "textarea"
    return "text"


def is_pii(label: str, value: str) -> bool:
    if PII_LABEL_RE.search(label):
        return True
    return any(p.search(value) for _, p in PII_VALUE_PATTERNS)


def heuristic_pairs(lines: list[str]) -> list[tuple[int, str, str]]:
    pairs = []
    rx = re.compile(r"^\s*([^:\n{}]{2,60}?)\s*:\s*(\S.*?)\s*$")
    for i, ln in enumerate(lines):
        m = rx.match(ln)
        if not m:
            continue
        label, value = m.group(1), m.group(2)
        if len(label.split()) > 8 or "{{" in value:
            continue
        pairs.append((i, label, value))
    return pairs


def slm_pairs(text: str, url: str, lines: list[str]) -> list[tuple[int, str, str]]:
    prompt = (
        "Del siguiente texto clinico oftalmologico en espanol, lista los campos EDITABLES "
        "(medidas, fechas, nombres, hallazgos que cambian entre pacientes). Responde SOLO JSON: "
        '{"campos":[{"label":"...","value":"texto exacto copiado del original"}]}\n\n' + text[:6000]
    )
    payload = json.dumps({
        "model": "template-assistant", "prompt": prompt, "stream": False, "format": "json",
        "options": {"temperature": 0.15},
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{url.rstrip('/')}/api/generate", data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    obj = json.loads(data.get("response", "{}"))
    out = []
    for c in obj.get("campos", []):
        label, value = str(c.get("label", "")).strip(), str(c.get("value", "")).strip()
        if not label or len(value) < 1:
            continue
        for i, ln in enumerate(lines):
            if value in ln:
                out.append((i, label, value))
                break
    return out


def detect_candidates(text: str, gdict: dict, use_slm: bool, ollama_url: str) -> list[dict]:
    lines = text.splitlines()
    idx = global_lookup(gdict)
    raw: list[tuple[int, str, str, str]] = []  # (line, label, value, source)

    for i, label, value in heuristic_pairs(lines):
        raw.append((i, label, value, "heuristica"))

    # Valores por defecto del diccionario global presentes en el texto
    for vid, spec in gdict.items():
        dv = str(spec.get("defaultValue", "")).strip()
        if len(dv) < 4:
            continue
        for i, ln in enumerate(lines):
            if dv in ln:
                raw.append((i, spec.get("label", vid), dv, "global"))
                break

    if use_slm:
        try:
            for i, label, value in slm_pairs(text, ollama_url, lines):
                raw.append((i, label, value, "slm"))
        except Exception as exc:  # LEGION apagada u otra falla: seguir con 0 tokens
            print(f"[INFO] SLM no disponible ({type(exc).__name__}); uso heuristica local.", file=sys.stderr)

    cands, seen_pos, used_ids = [], set(), {}
    for i, label, value, src in sorted(raw, key=lambda r: (r[0], r[3] != "global")):
        key = (i, value)
        if key in seen_pos or value not in lines[i]:
            continue
        seen_pos.add(key)
        gid = idx.get(norm_label(label)) or idx.get(slug(label))
        vid = gid or slug(label)
        in_global = gid is not None
        used_ids[vid] = used_ids.get(vid, 0) + 1
        if used_ids[vid] > 1:
            vid = f"{vid}_{used_ids[vid]}"
            in_global = False
        spec = gdict.get(vid, {}) if in_global else {}
        pii = is_pii(label, value)
        cands.append({
            "n": len(cands) + 1,
            "id": vid,
            "label": spec.get("label", label.strip()),
            "type": spec.get("type") or guess_type(value),
            "options": spec.get("options", []),
            "value": value,
            "orig": value,
            "line": i,
            "source": "global" if in_global else src,
            "in_global": in_global,
            "pii": pii,
        })
    return cands


# ----------------------------------------------------------------------------
# Sesiones (puente CLI <-> WebUI)
# ----------------------------------------------------------------------------

def save_session(sess: dict) -> Path:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    p = SESSIONS_DIR / f"{sess['id']}.json"
    p.write_text(json.dumps(sess, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def load_session(sid: str) -> dict:
    p = SESSIONS_DIR / f"{sid}.json"
    if not p.exists():
        raise SystemExit(f"Sesion no encontrada: {sid}")
    return json.loads(p.read_text(encoding="utf-8"))


def print_candidates(sess: dict) -> None:
    print(f"\nFuente: {sess['source']}  |  Sesion: {sess['id']}")
    print(f"{len(sess['candidates'])} variables candidatas:\n")
    for c in sess["candidates"]:
        flags = []
        if c["pii"]:
            flags.append("DATO PERSONAL")
        flags.append("global" if c["in_global"] else "nueva")
        val = c["value"] if len(c["value"]) <= 60 else c["value"][:57] + "..."
        print(f"  {c['n']:>2}. {{{{{c['id']}}}}} [{c['type']}] \"{val}\"  ({', '.join(flags)})")
    print()


def parse_selection(expr: str, total: int) -> list[int]:
    expr = expr.strip().lower()
    if expr in ("all", "todo", "todas"):
        return list(range(1, total + 1))
    out = []
    for part in re.split(r"[,\s]+", expr):
        if not part:
            continue
        m = re.fullmatch(r"(\d+)-(\d+)", part)
        if m:
            out.extend(range(int(m.group(1)), int(m.group(2)) + 1))
        elif part.isdigit():
            out.append(int(part))
        else:
            raise ValueError(f"Seleccion invalida: '{part}'")
    return sorted({n for n in out if 1 <= n <= total})


def apply_edit(cands: list[dict], edit: str) -> None:
    """edit: '3 id=foo label=Bar type=textarea default=xx'"""
    toks = shlex.split(edit)
    if toks and toks[0].lower() == "edit":
        toks = toks[1:]
    n = int(toks[0])
    c = next((x for x in cands if x["n"] == n), None)
    if not c:
        raise ValueError(f"No existe la variable {n}")
    for t in toks[1:]:
        k, _, v = t.partition("=")
        k = k.lower()
        if k == "id":
            c["id"], c["in_global"] = slug(v), False
        elif k == "label":
            c["label"] = v
        elif k == "type":
            if v not in VALID_TYPES:
                raise ValueError(f"Tipo invalido '{v}' ({', '.join(sorted(VALID_TYPES))})")
            c["type"] = v
        elif k in ("default", "defaultvalue"):
            c["value"], c["custom_default"] = v, True
        else:
            raise ValueError(f"Campo desconocido '{k}'")


# ----------------------------------------------------------------------------
# Construccion / export
# ----------------------------------------------------------------------------

def residual_pii(text: str) -> list[str]:
    found = []
    for name, rx in PII_VALUE_PATTERNS:
        for m in rx.finditer(text):
            found.append(f"{name}: {m.group(0)}")
    return found


POLICY_PATH = WEB_DIR / "politica_datos_personales.json"


def personal_allowed(stem: str, text: str, override: str = "auto") -> tuple[bool, str]:
    """Decide si la plantilla puede llevar nombre/ID/fecha. Devuelve (permitido, motivo)."""
    if override in ("yes", "no"):
        return override == "yes", f"--personal {override}"
    pol = {}
    if POLICY_PATH.exists():
        pol = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    s = slug(stem).upper()
    for k in pol.get("deny_stems", ["ADULTO", "CONSENTIMIENTO", "LACTANTE", "NEONATO", "PEDIATRICO"]):
        if k in s:
            return False, f"plantilla generica ({k})"
    for k in pol.get("allow_stems", ["RECOMENDACION", "RECETA", "FORMULA", "PRESCRIPCION"]):
        if k in s:
            return True, f"incluye receta/recomendaciones ({k})"
    rx = pol.get("allow_content_regex")
    if rx and re.search(rx, text, re.I):
        return True, "el texto incluye receta/recomendaciones"
    return False, "plantilla generica (por defecto)"


def strip_personal(sess: dict, lines: list[str], cands: list[dict]) -> tuple[list[dict], list[str]]:
    """Quita variables personales y las lineas 'Etiqueta: valor' que las contenian."""
    keep, drop_lines, removed = [], set(), []
    for c in cands:
        if c["pii"]:
            drop_lines.add(c["line"])
            removed.append(c["id"])
        else:
            keep.append(c)
    # Tambien las pares personales no elegidas
    for c in sess["candidates"]:
        if c["pii"]:
            drop_lines.add(c["line"])
    lines[:] = [ln for i, ln in enumerate(lines) if i not in drop_lines]
    # reindexar lineas de las variables conservadas
    shift = sorted(drop_lines)
    for c in keep:
        c["line"] -= sum(1 for d in shift if d < c["line"])
    return keep, removed


def build(sess: dict, picks: list[int], stem: str, title: str, dry_run: bool, allow_pii: bool,
          personal: str = "auto") -> int:
    cands = [c for c in sess["candidates"] if c["n"] in picks]
    if not cands:
        print("[ERROR] No se selecciono ninguna variable.")
        return 2

    lines = sess["text"].splitlines()
    allowed, why = personal_allowed(stem, sess["text"], personal)
    print(f"[POLITICA] Nombre/ID/fecha {'PERMITIDOS' if allowed else 'EXCLUIDOS'}: {why}")
    if not allowed:
        cands, removed = strip_personal(sess, lines, cands)
        if removed:
            print(f"[POLITICA] Variables personales descartadas: {', '.join(removed)}")
        if not cands:
            print("[ERROR] No quedan variables tras aplicar la politica.")
            return 2
    gdict = load_global()
    variables, used_ids = [], set()
    for c in sorted(cands, key=lambda x: x["line"]):
        if c["id"] in used_ids:
            continue
        used_ids.add(c["id"])
        i = c["line"]
        lines[i] = lines[i].replace(c["orig"], "{{" + c["id"] + "}}", 1)
        default = "" if c["pii"] else (gdict[c["id"]].get("defaultValue", c["value"]) if c["in_global"] and c["id"] in gdict and not c.get("custom_default") else c["value"])
        variables.append({
            "id": c["id"], "label": c["label"], "type": c["type"],
            "options": c.get("options", []), "defaultValue": default,
        })
    template_text = "\n".join(lines).strip()

    leftovers = residual_pii(template_text)
    if leftovers and not allow_pii:
        print("[BLOQUEADO] El texto aun contiene posibles datos personales sin convertir en variable:")
        for f in leftovers[:15]:
            print(f"   - {f}")
        print("Vuelva a seleccionar incluyendo esas variables (marcadas DATO PERSONAL) o use --allow-pii.")
        return 3

    stem = re.sub(r"[^A-Z0-9_]", "", slug(stem).upper()) or "PLANTILLA"
    title = title or stem.replace("_", " ").title()
    title, variables, template_text = B.normalize_template_data(stem, title, variables, template_text)

    out_dir = DRAFTS_DIR if dry_run else WEB_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    DRAFTS_DIR.mkdir(exist_ok=True)

    (DRAFTS_DIR / f"{stem}.txt").write_text(template_text + "\n", encoding="utf-8")
    base_web = B.derive_web_base_from_editor(relative_portal="../index.html")
    rendered = B.inject_into_html(base_web, title, variables, template_text, is_editor=False)
    (out_dir / f"{stem}.html").write_text(rendered, encoding="utf-8")

    # JSON por plantilla: SOLO las variables necesarias
    tpl_json = {
        "template": stem, "title": title, "lang": "es", "source": sess["source"],
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "variables": {v["id"]: {k: v[k] for k in ("label", "type", "options", "defaultValue")} for v in variables},
    }
    (out_dir / f"{stem}.json").write_text(json.dumps(tpl_json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Diccionario global: agregar solo variables nuevas elegidas
    if not dry_run:
        added = []
        for v in variables:
            if v["id"] not in gdict:
                gdict[v["id"]] = {k: v[k] for k in ("label", "type", "options", "defaultValue")}
                added.append(v["id"])
        save_global(gdict)
        if added:
            print(f"[GLOBAL] Nuevas variables en variables_globales.json: {', '.join(added)}")

    # Aprendizaje: registrar elecciones
    MEM_DIR.mkdir(exist_ok=True)
    with PICKS_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "ts": datetime.now().isoformat(timespec="seconds"), "template": stem,
            "picked": [v["id"] for v in variables],
            "skipped": [c["id"] for c in sess["candidates"] if c["n"] not in picks],
        }, ensure_ascii=False) + "\n")

    where = "borradores_sites/ (dry-run)" if dry_run else "web/"
    print(f"[OK] {where}{stem}.html + {stem}.json  ({len(variables)} variables)")
    if not dry_run:
        print("[SIGUIENTE] Revise la plantilla y publique con la skill `checkpoint` (push a GitHub Pages).")
    return 0


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def make_session(args) -> dict:
    text, label = import_source(args.source, args.text)
    if not text:
        raise SystemExit("El texto importado esta vacio.")
    gdict = load_global()
    cands = detect_candidates(text, gdict, use_slm=not args.no_slm, ollama_url=args.ollama_url)
    if not cands:
        raise SystemExit("No se detectaron variables candidatas. Pegue un texto con campos 'Etiqueta: valor'.")
    sess = {
        "id": uuid.uuid4().hex[:8], "created": datetime.now().isoformat(timespec="seconds"),
        "source": label, "text": text, "candidates": cands,
    }
    save_session(sess)
    return sess


def interactive(sess: dict, args) -> int:
    stem = args.name or input("Nombre de la plantilla (ej. CONSULTA_GLAUCOMA): ").strip()
    allowed, why = personal_allowed(stem, sess["text"], args.personal)
    print(f"[POLITICA] Nombre/ID/fecha {'PERMITIDOS' if allowed else 'EXCLUIDOS'}: {why}")
    print_candidates(sess)
    picks = None
    while picks is None:
        ans = input("Variables a usar (ej. 1,3,5-7 | all | edit N id=.. label=.. type=.. default=.. | q): ").strip()
        if ans.lower() in ("q", "salir"):
            return 1
        try:
            if ans.lower().startswith("edit"):
                apply_edit(sess["candidates"], ans)
                save_session(sess)
                print_candidates(sess)
            else:
                picks = parse_selection(ans, len(sess["candidates"]))
                if not picks:
                    print("Seleccion vacia."); picks = None
        except (ValueError, IndexError) as exc:
            print(f"[ERROR] {exc}")
    return build(sess, picks, stem, args.title, args.dry_run, args.allow_pii, args.personal)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="template-agent: plantillas AutoText (es | local | export html+json)")
    ap.add_argument("--import", dest="source", metavar="URL|ARCHIVO|-", help="Fuente a importar")
    ap.add_argument("--text", help="Texto pegado directamente (para WebUI)")
    ap.add_argument("--analyze", action="store_true", help="Solo analiza y guarda sesion (modo WebUI paso 1)")
    ap.add_argument("--select", nargs=2, metavar=("SESSION_ID", "SELECCION"), help="Construye con la seleccion (WebUI paso 2)")
    ap.add_argument("--edit", action="append", default=[], help='Ej: "3 id=foo label=Bar type=text default=x"')
    ap.add_argument("--name", help="Nombre de la plantilla (STEM)")
    ap.add_argument("--title", default="", help="Titulo legible")
    ap.add_argument("--dry-run", action="store_true", help="Escribe solo en borradores_sites/")
    ap.add_argument("--allow-pii", action="store_true", help="Permite datos personales residuales (no recomendado)")
    ap.add_argument("--personal", choices=["auto", "yes", "no"], default="auto",
                    help="Nombre/ID/fecha: auto = segun web/politica_datos_personales.json")
    ap.add_argument("--no-slm", action="store_true", help="Solo heuristica 0 tokens (sin LEGION)")
    ap.add_argument("--ollama-url", default=DEFAULT_OLLAMA)
    args = ap.parse_args()

    try:
        if args.select:
            sess = load_session(args.select[0])
            for e in args.edit:
                apply_edit(sess["candidates"], e)
            picks = parse_selection(args.select[1], len(sess["candidates"]))
            if not args.name:
                raise SystemExit("Falta --name para construir la plantilla.")
            return build(sess, picks, args.name, args.title, args.dry_run, args.allow_pii, args.personal)

        sess = make_session(args)
        if args.analyze or not sys.stdin.isatty():
            print_candidates(sess)
            print(f"SESSION_ID={sess['id']}")
            print('Siguiente: --select ' + sess["id"] + ' "1,3,5" --name NOMBRE_PLANTILLA')
            return 0
        return interactive(sess, args)
    except (ValueError, IndexError) as exc:
        print(f"[ERROR] {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())

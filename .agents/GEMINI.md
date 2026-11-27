## Bitácora de Decisiones

### [2026-08-30] - Activación de skills y actualización de proyectos
- **Conversación**: [ID](conversation://2071f00e-3e26-4a4e-984b-670bae124f0e)
- **Decisiones**: Se leyeron las skills globales, se revisaron todos los repositorios y se unificaron las bitácoras (GEMINI.md y agy_config.md) para todos los proyectos bajo Desarrollo/Proyectos.


### [2026-11-02] - Auditoría Integral y Actualización de Validador Gauntlet
- **Conversación**: [558346d9](conversation://558346d9-155f-43d7-a0a1-b19e5a07962a)
- **Decisiones**: Se actualizó `AGENTS.md` apuntando a `Autotext_Final.html`, se renovó el bloque `project-snapshot` y se sincronizó `test-quality.ps1`.

### [2026-11-08] - Unificación del motor v12+, mejoras de consulta (Restablecer/atajos) e impresión con marca de agua Verum
- **Conversación**: [78558019](conversation://78558019-8235-4e95-be17-12f73ca6bc1d)
- **Decisiones**: Se unificó el motor v12+ en todas las plantillas de raíz y `web/` con `Plantilla_Verum.svg` incrustada, se añadió el botón `🔄 Restablecer` (`Alt+R`) y atajos (`Alt+C`, `Alt+M`, `Alt+P`), se implementó `formatTextForPrint()` para estructurar secciones/medicamentos/firma al imprimir manteniendo texto 100% plano al copiar a Historia Clínica, se depuraron las 8 plantillas en `build_autotext.py` y se configuró `.nojekyll` y el remoto `github` para GitHub Pages.

### [2026-11-21] - Vista 2 Columnas con Separadores Clínicos, Emparejamiento OD/OI, Edición Exclusiva en AutoText y Flujo Híbrido Móvil → PC via URL (`#s=...`)
- **Conversación**: [42609aa9](conversation://42609aa9-6e21-4c95-bc82-00b507701799)
- **Decisiones**:
  - Se estandarizaron todas las plantillas clínicas (`web/*.html` y raíz salvo `Autotext_Final.html`) a **2 columnas** (Izquierda: Variables con separadores clínicos automáticos por sección, ancho completo para toda variable no diferenciada en par OD vs OI, mitad izquierda para OD y mitad derecha para OI | Derecha: Texto Editado con botones `"📋 Copiar minúscula"`, `"🔠 Copiar MAYÚSCULA"`, `"🖨️ Imprimir Documento"`).
  - Se restringió la edición de la plantilla exclusivamente a `Autotext_Final.html` (incorporando un selector para cargar cualquiera de las 8 plantillas existentes).
  - Se implementó el flujo de trabajo híbrido sin servidor (`#s=<base64_delta>` en la URL con `history.replaceState` en tiempo real y botón `📲 Enlace Híbrido` / `Alt+L`) para editar variables en un dispositivo móvil sobre GitHub Pages y abrir exactamente la misma URL con las variables ya editadas en un portátil o equipo de escritorio.


### [2026-11-26] - Agente interactivo `template-agent`, política de datos personales y validación Gauntlet `[6/6]`
- **Conversación**: [3aa52be1](conversation://3aa52be1-3610-48d8-9942-e5b73c1b3870)
- **Decisiones**:
  - Se creó `template_agent.py` (CLI interactivo + modo 2 pasos `--analyze`/`--select` para WebUI OpenClaw) fijo en `es | local | export html+json`, generando `web/<STEM>.html`, `web/<STEM>.json` (solo variables usadas) y `web/variables_globales.json`.
  - Se integró la skill `template-agent` y la política global de datos personales en `\\NAS-760025\Desarrollo\Agent\OpenClaw\AGENTS.md` y `TEMPLATE_AGENT.md` (datos personales de pacientes restringidos únicamente a `Master_Sheet` y `AppsScript`).
  - Se implementó `web/politica_datos_personales.json`: excluye nombre/ID/fecha de plantillas genéricas (`ADULTO`, `CONSENTIMIENTO`, `LACTANTE`, `NEONATO`, `PEDIATRICO`) y los restringe a plantillas con receta o recomendaciones.
  - Se eliminaron `nombre_paciente` y `documento_paciente` de `CONSENTIMIENTO_CATARATA`, `CONSENTIMIENTO_CHALAZION` y `CONSENTIMIENTO_PTERIGION` (raíz y `web/`).
  - Se añadió el paso `[6/6]` a `test-quality.ps1` para validar consistencia de `{{variables}}` y cumplimiento de la política de datos personales en `web/*.html`, y se verificó `python3` (`3.11.2`) en el NAS.

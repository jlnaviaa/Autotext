---
name: Autotext
description: Generador de Plantillas de Texto HTML Autocontenidas para documentacion clinica oftalmologica.
---

## Estado Actual (snapshot)
- **Fase**: produccion
- **Ultimo cambio**: 2026-11-26
- **Proximo paso**: Tutorial paso a paso para interactuar con template-agent (-local) en LEGION para crear y editar plantillas
- **Bloqueadores**: ninguno
- **Conversacion activa**: [3aa52be1](conversation://3aa52be1-3610-48d8-9942-e5b73c1b3870)

## Flujo de Trabajo
1. Usuario aporta borrador en `.txt` o edita en `Autotext_Final.html`.
2. Ejecutar `python build_autotext.py` (o `--from-txt archivo.txt`) para sincronizar `web/` y regenerar el portal `index.html`.
3. Verificar calidad con `pwsh -ExecutionPolicy Bypass -File .\test-quality.ps1`.
4. Guardar en `\\NAS-760025\Desarrollo\Proyectos\Autotext\` y publicar en Gitea / GitHub Pages.

> Para arquitectura detallada, variables clinicas e instrucciones de generacion:
> leer `CONTEXT.md` en este mismo directorio.
> Para historial de versiones (v1-v12):
> leer `CHANGELOG.md` en este mismo directorio.

---
name: Autotext
description: Generador de Plantillas de Texto HTML Autocontenidas para documentacion clinica oftalmologica.
---

## Estado Actual (snapshot)
- **Fase**: activo
- **Ultimo cambio**: 2026-11-07
- **Proximo paso**: Configurar Push Mirror a GitHub Pages para publicar index.html y plantillas web/
- **Bloqueadores**: ninguno
- **Conversacion activa**: [2aefd4c7](conversation://2aefd4c7-e610-49bf-a31f-bf312b69d107)

## Flujo de Trabajo
1. Usuario aporta borrador en `.txt` o edita en `Autotext_Final.html`.
2. Ejecutar `python build_autotext.py` (o `--from-txt archivo.txt`) para sincronizar `web/` y regenerar el portal `index.html`.
3. Verificar calidad con `pwsh -ExecutionPolicy Bypass -File .\test-quality.ps1`.
4. Guardar en `\\NAS-760025\Desarrollo\Proyectos\Autotext\` y publicar en Gitea / GitHub Pages.

> Para arquitectura detallada, variables clinicas e instrucciones de generacion:
> leer `CONTEXT.md` en este mismo directorio.
> Para historial de versiones (v1-v12):
> leer `CHANGELOG.md` en este mismo directorio.

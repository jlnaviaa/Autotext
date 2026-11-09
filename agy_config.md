---
name: Autotext
description: Generador de Plantillas de Texto HTML Autocontenidas para documentacion clinica oftalmologica.
---

## Estado Actual (snapshot)
- **Fase**: produccion
- **Ultimo cambio**: 2026-11-08
- **Proximo paso**: Publicar en GitHub Pages (`git push github main`) o agregar nuevas plantillas `.txt`
- **Bloqueadores**: ninguno
- **Conversacion activa**: [78558019](conversation://78558019-8235-4e95-be17-12f73ca6bc1d)

## Flujo de Trabajo
1. Usuario aporta borrador en `.txt` o edita en `Autotext_Final.html`.
2. Ejecutar `python build_autotext.py` (o `--from-txt archivo.txt`) para sincronizar `web/` y regenerar el portal `index.html`.
3. Verificar calidad con `pwsh -ExecutionPolicy Bypass -File .\test-quality.ps1`.
4. Guardar en `\\NAS-760025\Desarrollo\Proyectos\Autotext\` y publicar en Gitea / GitHub Pages.

> Para arquitectura detallada, variables clinicas e instrucciones de generacion:
> leer `CONTEXT.md` en este mismo directorio.
> Para historial de versiones (v1-v12):
> leer `CHANGELOG.md` en este mismo directorio.

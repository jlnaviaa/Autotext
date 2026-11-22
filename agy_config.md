---
name: Autotext
description: Generador de Plantillas de Texto HTML Autocontenidas para documentacion clinica oftalmologica.
---

## Estado Actual (snapshot)
- **Fase**: produccion
- **Ultimo cambio**: 2026-11-21
- **Proximo paso**: Compilar nuevas plantillas clinicas desde borradores `.txt` o usar flujo hibrido (`#s=...`) en consulta
- **Bloqueadores**: ninguno
- **Conversacion activa**: [42609aa9](conversation://42609aa9-6e21-4c95-bc82-00b507701799)

## Flujo de Trabajo
1. Usuario aporta borrador en `.txt` o edita en `Autotext_Final.html`.
2. Ejecutar `python build_autotext.py` (o `--from-txt archivo.txt`) para sincronizar `web/` y regenerar el portal `index.html`.
3. Verificar calidad con `pwsh -ExecutionPolicy Bypass -File .\test-quality.ps1`.
4. Guardar en `\\NAS-760025\Desarrollo\Proyectos\Autotext\` y publicar en Gitea / GitHub Pages.

> Para arquitectura detallada, variables clinicas e instrucciones de generacion:
> leer `CONTEXT.md` en este mismo directorio.
> Para historial de versiones (v1-v12):
> leer `CHANGELOG.md` en este mismo directorio.

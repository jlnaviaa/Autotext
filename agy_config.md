---
name: Autotext
description: Generador de Plantillas de Texto HTML Autocontenidas para documentacion clinica oftalmologica.
---

## Estado Actual (snapshot)
- **Fase**: mantenimiento
- **Ultimo cambio**: 2026-07-19
- **Proximo paso**: Crear nuevas plantillas a partir de archivos .txt del usuario
- **Bloqueadores**: ninguno
- **Conversacion activa**: [8da28716](conversation://8da28716-a3be-4509-8ee9-d65f7801b971)

## Flujo de Trabajo
1. Usuario aporta borrador en `.txt`
2. La IA aplica control de calidad del texto (ortografia, Phrase case, siglas medicas)
3. La IA genera nuevo `.html` autocontenido usando `Autotext_Final.html` como base
4. Guardar en `\\NAS-760025\Desarrollo\Proyectos\Autotext\`

> Para arquitectura detallada, variables clinicas e instrucciones de generacion:
> leer `CONTEXT.md` en este mismo directorio.
> Para historial de versiones (v1-v12):
> leer `CHANGELOG.md` en este mismo directorio.

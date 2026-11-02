# AGENTS.md — Autotext

Guía operativa para agentes de IA en este repositorio.

## 1. Stack y Arquitectura
- **Propósito:** Generador de Plantillas de Texto HTML Autocontenidas para documentacion clinica.
- **Tecnologías:** HTML5, CSS3, Vanilla JavaScript (Autocontenido sin librerias externas).
- **Entorno:** Cliente ligero Windows 11 + NAS Ugreen ARM64 (o LEGION si aplica ML).

## 2. Comandos Canónicos
- Validar sintaxis: pwsh -File test-quality.ps1
- Probar plantillas: Abrir Autotext_Final.html en navegador

## 3. Reglas Infranqueables de Seguridad y Rendimiento
- Todos los recursos CSS/JS deben ser inline y autocontenidos.
- Respeta el diccionario oftalmologico de variables clinicas.
- Sin dependencias de red externas (100% offline).
- **Ahorro de Contexto:** Mantener `agy_config.md` < 3 KB con bloque `project-snapshot`.
- **Validación Local (0 Tokens):** Correr `test-quality.ps1` antes de entregar código o hacer commit.

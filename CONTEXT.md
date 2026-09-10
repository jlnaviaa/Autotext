---
name: autotext-context
description: >
  Contexto tecnico profundo del proyecto Autotext: motor de plantillas HTML
  autocontenidas para documentacion clinica oftalmologica. Leer este archivo
  solo cuando se va a crear o modificar una plantilla HTML.
---

# Autotext — Contexto Tecnico (Capa 2)

## Arquitectura del Motor

A partir de la version v9, cada plantilla es un archivo HTML autocontenido:
- El motor de renderizado, los datos y las variables viven en el mismo .html
- Al guardar (Ctrl+S / boton "Guardar Plantilla"), el archivo se guarda con
  todos los cambios integrados permanentemente en el codigo fuente.
- 100% Offline, Vanilla JS/CSS, sin dependencias externas.

## Archivo Base Oficial

**`Autotext_Final.html`** — El lienzo en blanco para crear nuevas plantillas.
Contiene la logica v12 completa (adaptabilidad iframe, layout OD/OI, defaultValues).

## Archivos de Referencia Clave

| Archivo                         | Proposito                                                    |
|---------------------------------|--------------------------------------------------------------|
| `ADULTO_PLANTILLA.html`         | Referencia principal: 47 variables, layout OD/OI activo      |
| `CONSULTA_CATARATA_PREMIUM.html`| Referencia para consentimientos y consultas quirurgicas      |
| `Autotext_Final.html`           | Lienzo en blanco oficial para nuevas plantillas              |

Los archivos `.txt` son los borradores de texto plano originales de cada plantilla.

## Capacidades Clave del Motor (v12)

- **Auto-edicion en caliente**: edita texto y variables en tiempo real
- **Guardado en el propio archivo**: Ctrl+S integra los cambios en el HTML
- **Layout tres columnas**: Configuracion | Formulario | Resultado (pantalla completa)
- **Layout OD/OI**: campos con sufijo `_od`/`_oi` se agrupan en dos columnas
- **Adaptabilidad iframe**: al detectar Google Sites, oculta configuracion
- **defaultValue**: cada variable tiene un valor normal preestablecido
- **Editor interactivo**: resultado editable como mini-procesador de texto
- **Impresion membretada**: SVG de fondo con logotipo corporativo
- **Tipos de variable**: text, textarea, number, date, select

## Flujo de Creacion de Nuevas Plantillas

1. El usuario aporta el borrador en un archivo `.txt`
2. La IA realiza control de calidad del texto:
   - Corrige ortografia, acentuacion, puntuacion
   - Aplica formato tipo oracion / Phrase case
   - Respeta siglas medicas (OD, OI, PIO, YAG, DNI) y nombres propios
   - Mantiene estructura original (parrafos, saltos, tabulaciones) — NO Markdown
3. La IA toma `Autotext_Final.html` como base y:
   - Deduce las variables clinicas correspondientes
   - Configura tipos, opciones y defaultValues normales
   - Genera el nuevo archivo HTML autocontenido en el NAS

## Variables Clinicas Estandar (Oftalmologia)

Usar siempre IDs en snake_case. Convencion de sufijos:
- `_od` = Ojo Derecho | `_oi` = Ojo Izquierdo
- Sin sufijo = campo bilateral o administrativo

### Variables de Agudeza Visual
`od_av_sc_lejos`, `oi_av_sc_lejos` — AV sin correccion lejos
`od_av_cc_lejos`, `oi_av_cc_lejos` — AV con correccion lejos
`od_autorrefraccion_esfera`, `od_autorrefraccion_cilindro`, `od_autorrefraccion_eje`

### Variables de Examen Anterior
`od_cornea`, `oi_cornea` — Estado de la cornea
`od_cristalino`, `oi_cristalino` — Estado del cristalino
`od_conjuntiva`, `oi_conjuntiva`
`od_iris`, `oi_iris`
`od_pio`, `oi_pio` — Presion intraocular

### Variables de Examen Posterior
`od_vitreo`, `oi_vitreo`
`od_retina`, `oi_retina`
`od_papila`, `oi_papila`
`od_macula`, `oi_macula`

### Variables Administrativas y Diagnostico
`nombre_paciente`, `fecha_consulta`, `medico_tratante`
`diagnostico_principal`, `plan_tratamiento`
`procedimiento`, `ojo_a_operar`, `tipo_anestesia`

## Instrucciones para el Agente al Generar Plantillas

- Siempre tomar `Autotext_Final.html` como base (nunca modificar los archivos de referencia)
- Guardar los nuevos archivos en `\\NAS-760025\Desarrollo\Proyectos\Autotext\`
- Los archivos de la subcarpeta `web/` son versiones de produccion sin editor
- Nominar los archivos con nombre descriptivo: `NOMBRE_PLANTILLA.html`

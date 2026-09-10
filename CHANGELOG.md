# Autotext — Historial de Cambios (CHANGELOG)

Este archivo contiene el historial completo de iteraciones del proyecto.
No es necesario leerlo a menos que el usuario pregunte por el historial.

---

## Iteracion 1 — v1 a v3 (Versiones iniciales)
- Formulario y plantilla fijos (no dinamicos).
- Evolucion hasta autotextv3.html con layout basico de dos columnas.

## Iteracion 2 — v7 y v8 (Gestion multi-plantilla con localStorage)
- Se intento gestionar multiples plantillas en un unico archivo via localStorage.
- Se integro Bootstrap 5.3.3, Bootstrap Icons y SortableJS de CDN, luego inline.
- Problema: perdida de datos al renombrar el archivo .html exportado.
- Solucion: clave unica de localStorage basada en nombre de la primera plantilla.
- Problemas adicionales: ReferenceError en la v8 por refactorizacion incompleta,
  TypeError en aplicaciones exportadas al eliminar nodos del editor del DOM.

## Iteracion 3 — v9 (Nueva estrategia: un archivo por plantilla)
- Abandono de localStorage. Nueva estrategia: un HTML autocontenido por plantilla.
- El estado de variables se guarda en <script id="variables-data"> dentro del DOM.
- Guardado via Ctrl+S del navegador integra todos los cambios permanentemente.
- Motor 100% Vanilla JS/CSS sin dependencias externas.

## Iteracion 4 — v10 (Edicion de variables existentes)
- Boton de lapiz para editar ID, etiqueta, tipo y opciones de variables ya creadas.
- Migracion automatica de valores si se cambia el ID de una variable.

## Iteracion 5 — v11 (Textos preestablecidos / defaultValue)
- Concepto de "Texto Preestablecido" para cada variable.
- Al abrir la plantilla, los campos se auto-rellenan con valores normales.
- El medico solo modifica los hallazgos patologicos, agilizando la consulta.

## Iteracion 6 — v12 (Layout OD/OI + adaptabilidad iframe)
- Layout inteligente: campos con _od/_oi se agrupan en dos columnas automaticamente.
- Deteccion de iframe para Google Sites: oculta configuracion, diseño limpio de uso.
- Dashboard 100vh con tres columnas independientes y scrollbars propios.
- Esta es la version de produccion actual (Autotext_Final.html).

## Iteracion 7 — Versiones de produccion (subcarpeta web/)
- Creacion de rama feature/web-version con todas las plantillas en carpeta web/.
- En estas versiones se elimino la interfaz de configuracion y el boton de guardado.
- Diseño fijo de dos columnas para uso clinico limpio (sin modo edicion).
- Fecha: 19 de julio de 2026.

## Iteracion 8 — Creacion de plantillas clinicas finales
- CONSULTA_CATARATA_PREMIUM.html generada desde .txt con motor de v12.
- ADULTO_PLANTILLA.html reescrita: 47 variables, layout OD/OI, defaultValues normales.
- Correccion ortografica completa (silindro -> cilindro, trasparente -> transparente).

## IDs de Conversacion Historicos
- d5aee722-c5cd-4507-862e-7679fad11722 (sesion inicial)
- 69c48576-9066-4897-bdb8-ce55d221ac8d (2026-07-20)
- 2071f00e-3e26-4a4e-984b-670bae124f0e (2026-08-30 mantenimiento global)

# Proyecto AutoText - Generador de Plantillas de Texto

## Descripción General

Este proyecto consiste en una aplicación web autocontenida (se ejecuta directamente en el navegador sin necesidad de un servidor) que facilita la generación de documentos de texto a partir de plantillas predefinidas. El objetivo principal es agilizar la creación de informes clínicos, consentimientos informados y otros documentos repetitivos, permitiendo al usuario rellenar un formulario dinámico para generar un texto final listo para ser copiado y pegado en sistemas de historia clínica electrónica u otros editores.

A partir de la versión v9, el proyecto adopta la estrategia de **un archivo HTML autocontenido por plantilla**. Cada archivo HTML contiene tanto el motor de renderizado como los datos de su propia plantilla y variables. Esto permite crear archivos de plantilla independientes (ej: `Consentimiento catarata.html` o `Consentimiento iridotomia.html`) que guardan su configuración directamente en su propio código fuente al ser guardados desde el navegador, eliminando la necesidad de servidores o bases de datos externas.

## Fichero Principal y Uso

El lienzo en blanco oficial para diseñar cualquier nueva plantilla es **`autotext-final.html`**.

**Para crear una nueva plantilla:**
1.  Abra **`autotext-final.html`** en su navegador web.
2.  Escriba el título de la plantilla, redacte el texto base y configure sus variables.
3.  Pulse el botón **"Guardar Plantilla"** (o presione **Ctrl+S** en su navegador) para descargar/guardar un nuevo archivo HTML con el nombre específico de su plantilla (ej: `Examen_Clinico.html`).
4.  Este nuevo archivo será una aplicación autoeditable totalmente funcional por sí sola.

### Ficheros de Referencia Oficiales

Para el diseño de variables, sintaxis del texto base y configuración del layout de doble columna, se deben utilizar los siguientes ficheros del proyecto como modelo de referencia:
*   **`ADULTO_PLANTILLA.html`**: El modelo de referencia principal para exámenes clínicos extensos. Contiene 47 variables autogestionadas con sus textos normales preestablecidos entre comillas y el layout de doble columna (OD a la izquierda, OI a la derecha) plenamente operativo.
*   **`CONSULTA_CATARATA_PREMIUM.html`**: El modelo de referencia principal para consentimientos y consultas quirúrgicas avanzadas de catarata.

## Características Clave (`autotext-final.html` / `v12`)

El motor de plantillas cuenta con las siguientes características avanzadas:

-   **Auto-Edición en Caliente**: Permite editar el texto base de la plantilla y configurar sus variables en tiempo real. Al realizar cambios, la aplicación modifica su propio DOM y escribe su estado en un script JSON interno (`<script id="variables-data">`).
-   **Guardado en el propio Archivo**: Al hacer "Guardar como" (Ctrl+S) en el navegador o pulsar "Guardar Plantilla", el archivo se descarga con la configuración de variables y textos permanentemente integrados en el código.
-   **Configuración de Variables Avanzada**:
    -   Puedes **añadir, eliminar y editar** variables existentes mediante un botón ✏️ en la lista.
    -   Cada variable tiene un `id` único, una `label` descriptiva y un `type` específico (`text`, `textarea`, `number`, `date`, `select`).
    -   **Reordenación**: Permite cambiar el orden de las variables en el formulario mediante botones simples de subir ⬆️ y bajar ⬇️.
-   **Textos Preestablecidos (defaultValue)**: Permite definir un valor por defecto para cada variable (ej. "Córnea transparente"). Al abrir la aplicación, el formulario se auto-rellena con estos textos y el documento se genera de inmediato, permitiendo modificar solo los hallazgos patológicos.
-   **Layout en Tres Columnas (Modo Local)**: Presenta una distribución tipo dashboard a pantalla completa (`100vh`) con tres columnas independientes: Configuración (Izquierda) | Formulario (Centro) | Resultado Generado (Derecha). Cada columna tiene su propio scrollbar independiente, eliminando el scroll general de la ventana del navegador.
-   **Layout de Doble Columna (OD/OI)**: Dentro del formulario, los campos cuyos IDs terminen en `_od`/`_oi` (o etiquetas que contengan `OD`/`OI`) se agrupan automáticamente uno al lado del otro (Ojo Derecho a la izquierda, Ojo Izquierdo a la derecha), adaptándose perfectamente a la práctica oftalmológica.
-   **Adaptabilidad a Google Sites (Iframe)**: Al detectar que se ejecuta dentro de un iframe, la aplicación oculta automáticamente el encabezado y el panel de configuración, y pasa a un diseño de **dos columnas: Formulario (Izquierda) | Resultado (Derecha)** a pantalla completa sin scroll vertical del navegador.
-   **100% Offline y Vanilla**: Escrito enteramente en HTML5, CSS3 y JavaScript Vanilla, sin dependencias de librerías externas (sin Bootstrap, ni JQuery, ni SortableJS) ni conexiones a internet (CDNs), garantizando compatibilidad absoluta y carga instantánea.
-   **Funcionalidad de Copiado**: Botones para copiar el texto generado al portapapeles tal cual o convertido íntegramente a MAYÚSCULAS.

## Historial de Cambios

### 5 de julio de 2026

-   **Integración de Control de Versiones (Git)**:
    *   Inicialización del repositorio Git local en la rama principal `main` en la NAS.
    *   Creación del archivo `.gitignore` para excluir archivos temporales de sistema, office y desarrollo local.
    *   Realización del primer commit con la estructura limpia del motor de plantillas v12 y los archivos `.txt` de consulta.
-   **Impresión Clínica con Marca de Agua**:
    *   Incorporación de la hoja de estilo CSS `@media print` para ocultar la interfaz web y dar formato de carta limpio al texto del informe clínico al imprimir.
    *   Adición del botón "Imprimir Documento" que sincroniza el texto generado y abre el diálogo nativo de impresión.
    *   Integración de la marca de agua vectorial usando el logotipo corporativo `Plantilla_Verum.svg` posicionado en el centro de la página, sin rotación/inclinación, cubriendo la totalidad de la página (100% de alto y ancho en tamaño carta) con opacidad del 85% para asegurar su correcta visualización, configurando márgenes de página específicos (3 cm superior y 2 cm inferior, izquierdo y derecho).

### 29 de junio de 2026

-   **Mejora y Adaptación de Plantillas Clínicas**:
    *   **Creación de `CONSULTA_CATARATA_PREMIUM.html`**: Generada a partir de `CONSULTA_CATARATA_PREMIUM.txt` mediante el motor limpio de `autotext-final.html`, aplicando el control de calidad de ortografía, redacción y capitalización tipo oración.
    *   **Corrección y Reescritura de `ADULTO_PLANTILLA.html`**: Se alinearon los nombres de las variables de forma estricta con la sintaxis del archivo `ADULTO_PLANTILLA.txt` original (ej. `od_av_sc_lejos`, `od_autorrefraccion_cilindro`, etc.), corrigiendo fallos ortográficos (como "silindro", "trasparente" y "Sina") y de sintaxis en las llaves, y formateando a tipo oración.
    *   **Ampliación de Variables en `ADULTO_PLANTILLA.html`**: Se integraron todas las nuevas variables de exploración clínica (córnea, conjuntiva, iris, vítreo, retina, etc.) junto con sus valores preestablecidos definidos entre comillas por el usuario, resultando en una aplicación con 47 variables autogestionadas y con layout OD/OI activo.
    *   **Rediseño a Pantalla Completa (Dashboard `100vh`)**: Se eliminó el scroll vertical general del navegador en ordenadores y tabletas. El layout de la aplicación ahora distribuye el espacio en tres columnas independientes de altura fija (o dos columnas en modo iframe / Google Sites) con scrollbars independientes en las tarjetas del formulario y del resultado generado, manteniendo fijos y visibles los botones de copiado y el encabezado.

### 28 de junio de 2026

-   **Corrección Crítica y Rediseño de `autotext_gemini_v8.html`**:
    -   **Corrección de Error de Ejecución**: Se ha solucionado un error crítico de JavaScript (`ReferenceError`) que impedía por completo el funcionamiento de la lógica de la aplicación en la v8. El error se debía a una refactorización incompleta de los objetos que manejan los eventos y la renderización, dejando referencias a nombres de objetos antiguos. Esto hacía que la aplicación pareciera "muerta" (solo se veía el frontend).
    -   **Rediseño de la Interfaz**: Se ha reestructurado completamente el layout de la aplicación para mejorar el flujo de trabajo, dividiéndola en dos columnas principales:
        -   **Columna Izquierda**: Agrupa todas las herramientas de **edición y configuración**: gestión de plantillas, editor de texto de la plantilla, configuración de variables e importación/exportación.
        -   **Columna Derecha**: Se centra en el **uso y la visualización**: el formulario para rellenar las variables de la plantilla seleccionada y el área de texto con el resultado final y los botones de copiado.
-   **Mejora en `autotext_gemini_v8.html`**:
    -   Se ha modificado la función `exportApp` para que las aplicaciones exportadas como ficheros `.html` independientes tengan un `localStorage` más robusto.
    -   **Antes**: La clave de `localStorage` se basaba en el nombre del fichero, lo que provocaba que los datos se "perdieran" si el usuario cambiaba el nombre al fichero `.html`.
    -   **Ahora**: Se genera una clave única y persistente para el `localStorage` en el momento de la exportación, basada en el nombre de la primera plantilla seleccionada. Esto asegura que la aplicación exportada conserve sus datos aunque el fichero sea renombrado.
    -   El cambio se ha implementado modificando la plantilla de la aplicación exportable (`<template id="app-source-template">`) y la lógica de la función `exportApp`.
-   **Corrección de error en `autotext_gemini_v8.html`**:
    -   Se ha solucionado un error de JavaScript que impedía la correcta ejecución de la aplicación, especialmente al ser servida desde un servidor local (como Live Server).
    -   **Error**: Existía una referencia incorrecta a un elemento del DOM (`elements.newVarTypeInput` en lugar de `elements.newVarType`) que causaba un `TypeError` y detenía el script.
    -   **Solución**: Se ha corregido la referencia en el script principal y en la plantilla para aplicaciones exportadas, asegurando que la funcionalidad de mostrar/ocultar opciones para las variables de tipo "select" funcione correctamente y no impida la carga de la aplicación.
-   **Segunda Ronda de Correcciones y Mejoras en `autotext_gemini_v8.html`**:
    -   **Solución del Error Crítico de la Aplicación Exportada**: Se solucionó un error por el cual las aplicaciones independientes exportadas a HTML fallaban en el arranque con un `TypeError` al intentar asignar listeners a elementos del editor eliminados del DOM. Se implementó envolviendo la sección de exportación en `#export-app-section` y eliminando solo este elemento al exportar, manteniendo así la funcionalidad del editor y de variables en la aplicación exportada.
    -   **Persistencia del Estado de Selección**: Se actualizaron las funciones `saveState` y `loadState` para persistir la plantilla activa (`currentTemplate`) en `localStorage`. Al cargar o recargar la aplicación, ahora se inicializa y muestra automáticamente la última plantilla en uso (o la primera disponible), en lugar de presentar un formulario vacío que obligaba a pulsar "Cargar".
    -   **Validación de JSON Importado**: Se integró una validación de formato en `importJson` para evitar la inyección de datos corruptos al importar un backup.
    -   **Sanitización de IDs de Variables**: Se mejoró `addVar` para eliminar cualquier carácter que no sea alfanumérico ASCII o guion bajo, previniendo que los usuarios creen variables con caracteres especiales (como acentos o eñes) que luego la expresión de renderizado no pudiera reemplazar en el texto de la plantilla.
-   **Tercera Ronda: Conversión a Aplicación 100% Offline y Standalone**:
    -   **Integración de Librerías (Inline/Embed)**: Se descargaron e inyectaron directamente en el archivo HTML todas las dependencias de hojas de estilo y scripts (`Bootstrap 5.3.3 CSS`, `Bootstrap 5.3.3 JS` y `SortableJS 1.15.0`). Esto elimina por completo la necesidad de realizar peticiones HTTP a CDNs externas, garantizando que la aplicación cargue al instante incluso sin conexión a internet.
    -   **Reemplazo de Iconos por Emojis**: Se eliminó la dependencia de la tipografía web de `Bootstrap Icons` y se reemplazaron todas las etiquetas de iconos por emojis universales (ej. 📂, 📋, 🗑️, 🔠), asegurando que la interfaz sea visualmente rica y 100% funcional sin descargar archivos de fuentes.
    -   **Resiliencia ante Restricciones de Red (UNC/NAS)**: Se añadió un wrapper seguro sobre `localStorage` que, en caso de que el navegador bloquee el acceso por políticas de seguridad Same-Origin (común al abrir archivos `file://` desde una ruta compartida de red/NAS), conmuta automáticamente a un almacenamiento temporal en la memoria de la sesión para evitar que la aplicación deje de responder.
-   **Cuarta Ronda: Estrategia de Plantillas Auto-Editables Autocontenidas**:
    -   **Nueva Estrategia**: A petición del usuario y para evitar cualquier restricción del navegador con las rutas de red (NAS) y el uso de `localStorage`, se adopta la estrategia de **un archivo HTML por plantilla**.
    -   **Creación de `autotext_v9_autoeditable.html`**: Una versión 100% Vanilla CSS y JS (sin Bootstrap, ni JQuery, ni SortableJS, ni ninguna dependencia externa).
    -   **Mapeo Dinámico en el DOM**: El editor y el gestor de variables actualizan el DOM en tiempo real y escriben su estado de variables en un script JSON interno (`<script id="variables-data">`).
    -   **Flujo de Guardado**: El usuario puede modificar el título, el texto de la plantilla y sus variables. Luego, al hacer **"Guardar como" (Ctrl+S)** desde el menú de su navegador, o al pulsar el botón **"Guardar Plantilla"**, el archivo HTML se guarda localmente con todos los cambios ya integrados. Esto permite crear copias específicas e independientes de manera inmediata (ej. `Consentimiento catarata.html` o `Consentimiento iridotomia.html`), las cuales son 100% funcionales y editables por sí solas.
-   **Quinta Ronda: Edición de Variables y Textos Preestablecidos (v10 y v11)**:
    -   **Creación de `autotext_v10_autoeditable.html`**: Añade la capacidad de editar variables existentes mediante un botón de lápiz ✏️ en la lista de configuración. El formulario cambia dinámicamente a modo edición ("Editar Variable" / "Guardar Cambios") y permite modificar el ID, etiqueta, tipo y opciones, migrando automáticamente los valores existentes si se cambia el ID.
    -   **Creación de `autotext_v11_autoeditable.html`**: Introduce el concepto de **"Texto Preestablecido" (defaultValue)**. Permite definir un valor por defecto para cada variable (ej. "Cristalino claro en posición anatómica"). Al abrir la aplicación, los campos se rellenan automáticamente con estos textos y el documento se genera de inmediato, permitiendo al usuario modificar solo los hallazgos patológicos y agilizando drásticamente la consulta médica.
-   **Sexta Ronda: Layout de Doble Columna (OD/OI) y Adaptabilidad a Google Sites (v12)**:
    -   **Creación de `autotext_v12_autoeditable.html`**: Implementa una interfaz inteligente adaptativa y un diseño en dos columnas para datos clínicos de oftalmología (Ojo Derecho y Ojo Izquierdo).
    -   **Doble Columna (OD/OI)**: Los campos del formulario clínico cuyos IDs terminen en `_od`/`_oi` (o etiquetas que contengan `OD`/`OI`) se agrupan automáticamente uno al lado del otro (OD a la izquierda, OI a la derecha), imitando el aspecto de `autotextv3.html`. Las variables generales (nombre, fecha) o textareas se expanden al ancho completo.
    -   **Adaptabilidad a Google Sites (Iframe)**: Al detectar que la página se ejecuta dentro de un iframe (como en Google Sites), la aplicación oculta automáticamente la columna de configuración y la cabecera de guardado, adaptando el diseño a una única columna limpia de solo lectura/relleno ideal para la incrustación y el uso clínico diario sin distracciones.

## Descripción de Ficheros

-   **`CONSULTA_CATARATA.html`**: La aplicación autoeditable e interactiva de la Consulta de Catarata, generada a partir de `CONSULTA_CATARATA.txt` y `autotext-final.html`.
-   **`CONSULTA_CATARATA.txt`**: El borrador en texto plano original para la consulta de catarata.
-   **`CONSULTA_CATARATA_INSUMOS.html`**: La aplicación autoeditable e interactiva de la Consulta de Catarata con Insumos, generada a partir de `CONSULTA_CATARATA_INSUMOS.txt` y `autotext-final.html`.
-   **`CONSULTA_CATARATA_INSUMOS.txt`**: El borrador en texto plano original para la consulta de catarata con insumos.
-   **`ADULTO_PLANTILLA.html`**: La aplicación autoeditable e interactiva del Examen Clínico de Adulto, generada a partir de `ADULTO_PLANTILLA.txt` y `autotext-final.html`.
-   **`ADULTO_PLANTILLA.txt`**: El borrador en texto plano original para el examen de adultos.
-   **`CONSULTA_CATARATA_PREMIUM.html`**: La aplicación autoeditable e interactiva de la Consulta Prequirúrgica de Catarata (Premium), generada a partir de `CONSULTA_CATARATA_PREMIUM.txt` y `autotext-final.html`.
-   **`CONSULTA_CATARATA_PREMIUM.txt`**: El borrador en texto plano original aportado por el usuario.
-   **`autotext-final.html`**: **El lienzo en blanco oficial para crear nuevas plantillas.** Contiene la misma lógica avanzada de la v12 (adaptabilidad a Google Sites, layout de dos columnas OD/OI, edición y creación de variables con valores preestablecidos) pero inicia completamente en blanco (sin variables ni textos predefinidos) para que puedas diseñar cualquier plantilla desde cero y guardarla con su nombre correspondiente.
-   **`autotext_v12_autoeditable.html`**: Versión recomendada preconfigurada para Oftalmología. Combina la adaptabilidad a Google Sites (oculta la configuración cuando está incrustada), el layout de dos columnas para Ojo Derecho (OD) y Ojo Izquierdo (OI) al estilo de `autotextv3.html`, la edición de variables (v10) y los textos preestablecidos para hallazgos normales (v11).
-   **`autotext_v11_autoeditable.html`**: Versión anterior auto-editable que introdujo la posibilidad de añadir "textos preestablecidos" (valores por defecto).
-   **`autotext_v10_autoeditable.html`**: Versión anterior que introdujo la capacidad de editar variables ya existentes mediante el botón ✏️.
-   **`autotext_v9_autoeditable.html`**: La primera versión auto-editable basada en la nueva estrategia de guardar el DOM completo del archivo.
-   **`autotext_gemini_v8.html`**: Versión anterior que intentaba gestionar múltiples plantillas en un único archivo mediante `localStorage` y librerías CDNs integradas offline.
-   **`autotext_gemini_v7.html`**: Una versión anterior de la aplicación, que fue la base para el desarrollo de la v8.
-   **`autotextv3.html`**: Una versión anterior de la aplicación, superada por la v7.
-   **`autotextv2.1.html` / `autotextv2.html`**: Versiones aún más antiguas de desarrollo de plantillas.
-   **`autotextv1.html`**: La primera versión, con un formulario y una plantilla fijos (no dinámicos).
-   **`blueprint-engine.html`**: Un prototipo o versión de desarrollo inicial.
-   **`Prequirúrgico.txt`**: Un ejemplo de un texto de plantilla extenso.
-   **`VS-AutoText Pro - Engine_Consentimiento catarata.html`**: Copia de referencia.
-   **`dónde puedo encontrar las nombres de las variables.docx`**: Documento explicativo de variables.
-   **`gemini.md`**: Este mismo fichero de documentación, actualizado.

## Flujo de Trabajo para Nuevas Plantillas

A partir del análisis de las necesidades del usuario, se establece el siguiente flujo de trabajo para la creación de nuevas plantillas:

1.  **Aportación del Texto**: El usuario coloca un archivo de texto en formato plano (**`.txt`**) en la carpeta de trabajo con el borrador del consentimiento o informe.
2.  **Control de Calidad del Texto (IA)**: Antes de generar cualquier código, la IA realiza un procesamiento del texto en el que:
    *   Corrige la **ortografía** y la **redacción** médica.
    *   Aplica formato de **tipo oración / Phrase case** (capitalización donde solo la primera letra de cada frase inicia en mayúscula, respetando siglas médicas universales como *OD*, *OI*, *PIO*, *DNI*, *YAG* y nombres propios).
    *   Mantiene intacta la estructura original del texto (párrafos, saltos de línea, tabulaciones), evitando convertirlo a formato Markdown para no alterar la maquetación del usuario.
3.  **Generación de la Aplicación**: La IA toma el motor limpio de [autotext-final.html](file:////NAS-760025/personal_folder/Proyectos/Autotext/autotext-final.html), deduce y configura las variables clínicas correspondientes (con sus opciones y textos preestablecidos normales) y genera un nuevo archivo HTML autocontenido en la NAS.

## Identificador de conversación

agy --conversation=d5aee722-c5cd-4507-862e-7679fad11722
# AutoText - Generador de Plantillas de Texto Clínicas y Quirúrgicas

AutoText es una herramienta web **100% offline, autocontenida y sin dependencias externas**, diseñada específicamente para facilitar la generación de textos editados mediante variables, consentimientos informados y cualquier documento repetitivo. Permite a los profesionales médicos rellenar formularios dinámicos y generar de inmediato un texto final formateado y listo para copiar, pegar o imprimir.

A partir de la versión **v12**, el motor de la aplicación incrusta directamente todos sus recursos y lógica de procesamiento en el propio archivo HTML, lo que permite que cada plantilla descargada sea una aplicación autoeditable totalmente independiente y portable.

---

## 🚀 Características Clave (Motor v12)

*   **Auto-Edición en Caliente**: Configura variables y redacta el texto base directamente desde el navegador. Al hacer clic en **"Guardar Plantilla" (o presionar Ctrl+S)**, se descarga un nuevo archivo HTML que integra permanentemente tus cambios de código y variables en su DOM interno (`<script id="variables-data">`).
*   **100% Offline y Portable (Vanilla JS & CSS)**: No requiere conexiones a Internet, servidores web ni bases de datos. Tampoco utiliza dependencias CDNs (como Bootstrap o jQuery), lo que garantiza que cargue de forma instantánea en cualquier ordenador, tableta o red local compartida (NAS).
*   **Impresión Clínica con Membrete y Marca de Agua**: Permite imprimir el texto editado mediante variables usando un botón dedicado. La aplicación aplica automáticamente una hoja de estilo `@media print` que oculta el panel de control y superpone el texto médico sobre la marca de agua corporativa (`Plantilla_Verum.svg`). Dicha imagen está incrustada en Base64 para garantizar que se imprima correctamente en Chrome, Edge y Safari sin depender de archivos externos o de la opción "Gráficos de fondo".
*   **Valores Preestablecidos (Default Values)**: Permite configurar respuestas por defecto para los hallazgos normales (ej: *"Córnea transparente"*). Al abrir la plantilla, el formulario se autocompleta con estas descripciones normales de inmediato, permitiendo al médico modificar únicamente las patologías encontradas y agilizando drásticamente la consulta.
*   **Distribución Inteligente en Dos Columnas (OD/OI)**: Los campos de exploración clínica cuyos IDs o etiquetas contengan terminaciones como `_od`/`_oi` (Ojo Derecho / Ojo Izquierdo) se agrupan automáticamente lado a lado, emulando la distribución de las fichas clínicas oftalmológicas tradicionales.
*   **Adaptabilidad a Google Sites (Iframe)**: La aplicación detecta si se está ejecutando dentro de un iframe. En ese caso, oculta automáticamente el panel de configuración de la izquierda y la cabecera, ofreciendo un diseño limpio y optimizado a pantalla completa de solo rellenado y generación.
*   **Miniprocesador de Textos Generados**: El resultado final se muestra en una caja interactiva (`contenteditable`) que permite realizar ajustes, correcciones ortográficas o añadir comentarios de último minuto antes de copiar el texto final en mayúsculas o minúsculas.

---

## 📂 Archivos Principales del Proyecto

*   **[Autotext_Final.html](./Autotext_Final.html)** - [▶️ Abrir Lienzo (App)](https://jlnaviaa.github.io/Autotext/Autotext_Final.html): **El lienzo oficial en blanco.** Utilízalo para crear cualquier nueva plantilla desde cero. Escribe tu texto, define las variables y descárgalo con el nombre específico del documento.
*   **[ADULTO_PLANTILLA.html](./ADULTO_PLANTILLA.html)** - [▶️ Abrir Editor](https://jlnaviaa.github.io/Autotext/ADULTO_PLANTILLA.html) | [🌐 Versión Web Limpia](https://jlnaviaa.github.io/Autotext/web/ADULTO_PLANTILLA.html): Modelo clínico de referencia principal para exámenes extensos (47 variables autogestionadas con layout OD/OI).
*   **[CONSULTA_CATARATA_PREMIUM.html](./CONSULTA_CATARATA_PREMIUM.html)** - [▶️ Abrir Editor](https://jlnaviaa.github.io/Autotext/CONSULTA_CATARATA_PREMIUM.html) | [🌐 Versión Web Limpia](https://jlnaviaa.github.io/Autotext/web/CONSULTA_CATARATA_PREMIUM.html): Modelo de referencia principal para consentimientos y consultas quirúrgicas avanzadas.
*   **[CONSULTA_CATARATA.html](./CONSULTA_CATARATA.html)** - [▶️ Abrir Editor](https://jlnaviaa.github.io/Autotext/CONSULTA_CATARATA.html) | [🌐 Versión Web Limpia](https://jlnaviaa.github.io/Autotext/web/CONSULTA_CATARATA.html): Plantilla interactiva de la consulta de catarata.
*   **[Plantilla_Verum.svg](./Plantilla_Verum.svg)**: Hoja membretada e imagen de fondo corporativo utilizada para la impresión clínica.
*   **[web/](./web/)**: Subcarpeta que contiene versiones de producción de las plantillas (solo lectura/relleno). Estas versiones están libres de la interfaz de configuración (panel izquierdo y guardado) y fijadas en un diseño limpio de dos columnas.

---

## 🛠️ Flujo de Trabajo para Crear Nuevas Plantillas

1.  **Redacción del Borrador**: Escribe o edita el texto en formato plano (`.txt`) del consentimiento o informe.
2.  **Control de Calidad del Texto (IA)**:
    *   Corrige la ortografía y redacción médica.
    *   Aplica capitalización de **tipo oración / phrase case** (solo la primera letra de cada frase en mayúsculas, respetando siglas universales como *OD*, *OI*, *PIO*, *DNI*, *YAG* y nombres propios).
    *   Conserva saltos de línea y tabulaciones originales.
3.  **Generación de la Plantilla**:
    *   Abre **[Autotext_Final.html](https://jlnaviaa.github.io/Autotext/Autotext_Final.html)** en el navegador.
    *   Introduce el título de la plantilla.
    *   Copia y pega el texto depurado en la pestaña **"Editar Texto"** usando la sintaxis `{{nombre_variable}}`.
    *   Agrega y define las variables en la pestaña **"Configurar Variables"** (asigna tipos de datos, opciones para listas y valores por defecto).
    *   Haz clic en **"💾 Guardar Plantilla"** (o presiona **Ctrl+S**) para descargar la aplicación autocontenida con el nombre correspondiente (ej: `Examen_Clinico.html`).

---

## 💻 Desarrollo y Control de Versiones

El proyecto cuenta con un repositorio Git local en la NAS (rama `main`). Para realizar tareas o restaurar conversaciones anteriores con la CLI de desarrollo de Gemini (**agy**), puedes ejecutar en la terminal de tu sistema:

---
*Desarrollado con amor por la práctica médica eficiente y sin servidores.*

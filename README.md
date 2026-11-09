# AutoText v12 — Generador de Plantillas Clínicas y Quirúrgicas (HC + Impresión Membretada)

AutoText es una herramienta web **100% offline, autocontenida y sin dependencias externas**, diseñada para automatizar la documentación clínica oftalmológica con `{{variables}}` en dos flujos de trabajo simultáneos:

1. **Copiado directo a Software de Historia Clínica (EHR)**: Genera **texto 100% plano** (en formato normal o en MAYÚSCULAS) libre de etiquetas HTML o sintaxis Markdown (`##`, `**`, `---`), listo para pegar en cualquier sistema de historia clínica electrónica.
2. **Impresión Inmediata con Marca Personal (`Plantilla_Verum.svg`)**: Formatea automáticamente el documento exclusivamente al imprimir (`@media print`), aplicando encabezados clínicos en negrita, bloques destacados para medicamentos oftálmicos (`OFTAMOX`, `CORTIOFTAL`, `NEPAOFTAL`), fecha opcional y bloque de firma médica sobre la marca de agua corporativa incrustada en Base64.

---

## ⚡ Nuevas Mejoras Implementadas (Motor v12+)

* **Botón `🔄 Restablecer` (`Alt+R`)**: Restaura instantáneamente todas las variables del formulario a sus valores fisiológicos por defecto (incluyendo fecha actual automática para campos de tipo `date`) y limpia cualquier edición manual previa entre un paciente y el siguiente.
* **Atajos de Teclado de Consulta Rápida**:
  * `Alt+C`: Copiar texto plano limpio para Historia Clínica.
  * `Alt+M`: Copiar texto plano en MAYÚSCULAS.
  * `Alt+P`: Imprimir de inmediato con la marca de agua `Plantilla_Verum.svg`.
  * `Alt+R`: Restablecer formulario a valores por defecto.
  * `Ctrl+S`: Guardar plantilla HTML autoeditable (Modo Editor).
* **Impresión Editorial Inteligente (`formatTextForPrint`)**: Mientras que la vista en pantalla y el portapapeles conservan texto 100% plano para la historia clínica, el modo de impresión estructura visualmente títulos de sección, listas numeradas de recomendaciones postoperatorias, bloques de medicamentos y firma del **Dr. José Luis Navia Ávila** (con casillas activables de *Encabezado y fecha* y *Firma médica al imprimir*).
* **Detección Precisa en 2 Columnas (OD / OI)**: Agrupa automáticamente lado a lado los campos de Ojo Derecho y Ojo Izquierdo mediante coincidencia exacta de tokens (`_od`, `_oi`, `od_`, `oi_`), evitando falsos positivos en palabras que contienen esas sílabas.
* **Portal Clínico Interactvo (`index.html`)**: Catálogo con buscador en tiempo real, filtros por especialidad (*Consulta*, *Catarata*, *Quirúrgico*, *Fórmulas / Postop*), barra de atajos de teclado y acceso directo a **🌐 Modo Consulta / Imprimir** (`web/*.html`) y **✏️ Modo Editor** (`*.html`).

---

## 📂 Catálogo de Plantillas Sincronizadas (Raíz y `web/`)

* **[index.html](./index.html)** — [🌐 Abrir Portal en GitHub Pages](https://jlnaviaa.github.io/Autotext/): Punto de entrada principal con buscador y filtros.
* **[Autotext_Final.html](./Autotext_Final.html)** — Lienzo oficial en blanco para crear nuevas plantillas.
* **[ADULTO_PLANTILLA.html](./ADULTO_PLANTILLA.html)** ([Modo Consulta](./web/ADULTO_PLANTILLA.html)) — *Examen Clínico de Adulto* (47 variables con distribución OD/OI).
* **[CONSULTA_CATARATA.html](./CONSULTA_CATARATA.html)** ([Modo Consulta](./web/CONSULTA_CATARATA.html)) — *Consulta de Catarata* (8 variables).
* **[CONSULTA_CATARATA_INSUMOS.html](./CONSULTA_CATARATA_INSUMOS.html)** ([Modo Consulta](./web/CONSULTA_CATARATA_INSUMOS.html)) — *Consulta Catarata e Insumos Especiales* (10 variables).
* **[CONSULTA_CATARATA_PREMIUM.html](./CONSULTA_CATARATA_PREMIUM.html)** ([Modo Consulta](./web/CONSULTA_CATARATA_PREMIUM.html)) — *Consulta de Catarata y Lentes Premium* (14 variables).
* **[Prequirurgico.html](./Prequirurgico.html)** ([Modo Consulta](./web/Prequirurgico.html)) — *Valoración Prequirúrgica de Catarata* (14 variables).
* **[CIRUGIA.html](./CIRUGIA.html)** ([Modo Consulta](./web/CIRUGIA.html)) — *Descripción Quirúrgica y Fórmula de Facoemulsificación* (4 variables).
* **[Descripcion_Recomendaciones_Formula.html](./Descripcion_Recomendaciones_Formula.html)** ([Modo Consulta](./web/Descripcion_Recomendaciones_Formula.html)) — *Descripción Quirúrgica, Recomendaciones y Fórmula Tórica* (14 variables).
* **[RECOMENDACIONES_CATARATA.html](./RECOMENDACIONES_CATARATA.html)** ([Modo Consulta](./web/RECOMENDACIONES_CATARATA.html)) — *Recomendaciones Postoperatorias de Catarata* (5 variables).

---

## 🛠️ Compilación y Sincronización Automática (`build_autotext.py`)

Para sincronizar todas las plantillas entre el Modo Editor (raíz), el Modo Consulta (`web/`) y regenerar el portal `index.html`:

```powershell
python build_autotext.py
```

Para compilar una nueva plantilla directamente desde un borrador `.txt` con `{{variables}}`:

```powershell
python build_autotext.py --from-txt Mi_Borrador.txt --output NUEVA_PLANTILLA.html
```

---

## 🌐 Publicación en GitHub Pages y Gitea (NAS)

El repositorio incluye `.nojekyll` y enlaces relativos compatibles con **GitHub Pages** (`https://jlnaviaa.github.io/Autotext/`):

1. **Repositorio Primario (Gitea en NAS)**: `ssh://git@NAS-760025.local:2222/jlnaviaa/Autotext.git`
2. **Despliegue en GitHub Pages**:
   * Opción A (Push directo al remoto `github`): `git push github main`
   * Opción B (Push Mirror automático desde Gitea): En Gitea (`Settings -> Repository -> Mirror Settings`), agregar destino `https://github.com/jlnaviaa/Autotext.git` con tu Personal Access Token (PAT) y activar *Sync when commits are pushed*. En GitHub (`Settings -> Pages`), seleccionar `Deploy from a branch: main / (root)`.

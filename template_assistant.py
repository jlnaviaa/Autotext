#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
template_assistant.py — Agente Local Entrenable para Plantillas Clínicas AutoText v12
Integrado con:
- Google Sites Ingestion (https://sites.google.com/view/jlnaviaa-md/consulta y subpáginas)
- OpenClaw 1.5.0.0034 en NAS-760025 (:18799) con Cola Diferida (Offline/Wake Queue)
- Ollama SLM en LEGION (:11434 — modelo 'template-assistant' sobre RTX 5070 8GB VRAM + 32GB RAM)
- Bucle de Auto-Aprendizaje (--learn): detecta ediciones y mejoras realizadas por el
  Dr. José Luis Navia Ávila en las plantillas HTML, construye el dataset few-shot
  (training_memory/feedback_dataset.jsonl) y actualiza Modelfile.template-assistant.
"""

import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

import build_autotext

ROOT = Path(__file__).parent
WEB_DIR = ROOT / "web"
SITES_DRAFTS_DIR = ROOT / "borradores_sites"
MEMORY_DIR = ROOT / "training_memory"
SNAPSHOTS_PATH = MEMORY_DIR / "template_snapshots.json"
LEARNED_PREFS_PATH = MEMORY_DIR / "learned_preferences.json"
FEEDBACK_JSONL_PATH = MEMORY_DIR / "feedback_dataset.jsonl"
PENDING_QUEUE_PATH = MEMORY_DIR / "pending_legion_queue.json"
MODELFILE_PATH = ROOT.parent / "SLM_local" / "Modelfile.template-assistant"

GOOGLE_SITES_URLS = {
    "plantillas": "https://sites.google.com/view/jlnaviaa-md/consulta/plantillas",
    "consentimiento_catarata": "https://sites.google.com/view/jlnaviaa-md/consentimiento/catarata",
    "postoperatorio": "https://sites.google.com/view/jlnaviaa-md/consulta/postoperatorio",
    "patologia": "https://sites.google.com/view/jlnaviaa-md/consulta/patologia",
    "medicamentos": "https://sites.google.com/view/jlnaviaa-md/consulta/medicamentos",
    "procedimientos_pterigion": "https://sites.google.com/view/jlnaviaa-md/procedimientos/pterigion",
}


# =============================================================================
# 1. DEFINICIÓN DE PLANTILLAS CAPTURADAS DE GOOGLE SITES (jlnaviaa-md)
#    (Separadas en ficheros HTML individuales, 2 columnas, OD izq / OI der / AO 100%)
# =============================================================================

SITES_TEMPLATES_SPEC = [
    {
        "stem": "EXAMEN_NEONATO",
        "title": "Examen Oftalmológico de Neonato",
        "source_url": "https://sites.google.com/view/jlnaviaa-md/consulta/plantillas",
        "variables": [
            {"id": "antecedentes_neonato", "label": "Antecedentes Perinatales y Oculares", "type": "textarea", "defaultValue": "Niega antecedentes perinatales u oculares patológicos."},
            {"id": "agudeza_visual_ao", "label": "Agudeza Visual (Ambos Ojos)", "type": "text", "defaultValue": "Pupilas reactivas"},
            {"id": "parpado_od", "label": "Examen Externo OD", "type": "text", "defaultValue": "Bordes palpebrales normales. Puntos lagrimales bien. Pestañas normal."},
            {"id": "parpado_oi", "label": "Examen Externo OI", "type": "text", "defaultValue": "Bordes palpebrales normales. Puntos lagrimales bien. Pestañas normal."},
            {"id": "mov_ext", "label": "Movimientos Extraoculares", "type": "text", "defaultValue": "Hirschberg centrado."},
            {"id": "biomicroscopia_ao", "label": "Biomicroscopía (Ambos Ojos)", "type": "text", "defaultValue": "Conjuntiva sana. Córnea transparente. Cámara anterior formada, amplia. Iris con adecuada reactividad con midriasis farmacológica."},
            {"id": "cristalino_od", "label": "Cristalino OD", "type": "text", "defaultValue": "Cristalino claro en posición anatómica."},
            {"id": "cristalino_oi", "label": "Cristalino OI", "type": "text", "defaultValue": "Cristalino claro en posición anatómica."},
            {"id": "fondo_ojo_ao", "label": "Fondo de Ojo (Ambos Ojos)", "type": "text", "defaultValue": "Midriasis farmacológica con lente de 20 DP e indirecto: vítreo transparente. Retina adherida en toda su extensión, vascularizada hasta la periferia."},
            {"id": "excavacion_od", "label": "Excavación OD", "type": "text", "defaultValue": "0.3"},
            {"id": "excavacion_oi", "label": "Excavación OI", "type": "text", "defaultValue": "0.3"},
            {"id": "pio_conducta", "label": "Presión Intraocular", "type": "text", "defaultValue": "No se toma por edad del paciente."},
        ],
        "template_text": (
            "Antecedentes\n"
            "{{antecedentes_neonato}}\n\n"
            "Examen Oftalmológico\n"
            "Agudeza visual\n"
            "Ambos ojos: {{agudeza_visual_ao}}\n\n"
            "Examen externo\n"
            "Ojo derecho. {{parpado_od}}\n"
            "Ojo izquierdo. {{parpado_oi}}\n\n"
            "Movimientos extraoculares\n"
            "{{mov_ext}}\n\n"
            "Biomicroscopía\n"
            "Ambos ojos. {{biomicroscopia_ao}}\n"
            "Ojo derecho. {{cristalino_od}}\n"
            "Ojo izquierdo. {{cristalino_oi}}\n\n"
            "Polo posterior\n"
            "Ambos ojos. {{fondo_ojo_ao}}\n"
            "Ojo derecho. Excavación {{excavacion_od}}\n"
            "Ojo izquierdo. Excavación {{excavacion_oi}}\n\n"
            "Presión intraocular\n"
            "{{pio_conducta}}"
        ),
    },
    {
        "stem": "EXAMEN_LACTANTE",
        "title": "Examen Oftalmológico de Lactante",
        "source_url": "https://sites.google.com/view/jlnaviaa-md/consulta/plantillas",
        "variables": [
            {"id": "antecedentes_lactante", "label": "Antecedentes Generales y Oculares", "type": "textarea", "defaultValue": "Niega antecedentes patológicos, quirúrgicos u oculares de importancia."},
            {"id": "agudeza_visual_ao", "label": "Agudeza Visual Lejos SC (Ambos Ojos)", "type": "text", "defaultValue": "Fija, sigue y mantiene"},
            {"id": "parpado_od", "label": "Examen Externo OD", "type": "text", "defaultValue": "Bordes palpebrales normales. Puntos lagrimales bien. Pestañas normal."},
            {"id": "parpado_oi", "label": "Examen Externo OI", "type": "text", "defaultValue": "Bordes palpebrales normales. Puntos lagrimales bien. Pestañas normal."},
            {"id": "mov_ext", "label": "Movimientos Extraoculares", "type": "text", "defaultValue": "Hirschberg centrado. Cover test negativo."},
            {"id": "biomicroscopia_ao", "label": "Biomicroscopía (Ambos Ojos)", "type": "text", "defaultValue": "Conjuntiva sana. Córnea transparente. Cámara anterior formada, amplia. Iris normal."},
            {"id": "cristalino_od", "label": "Cristalino OD", "type": "text", "defaultValue": "Cristalino claro en posición anatómica."},
            {"id": "cristalino_oi", "label": "Cristalino OI", "type": "text", "defaultValue": "Cristalino claro en posición anatómica."},
            {"id": "fondo_ojo_ao", "label": "Fondo de Ojo (Ambos Ojos)", "type": "text", "defaultValue": "Vítreo transparente. Retina adherida. Disco de aspecto normal. Vasculatura sana."},
            {"id": "excavacion_od", "label": "Excavación OD", "type": "text", "defaultValue": "0.3"},
            {"id": "excavacion_oi", "label": "Excavación OI", "type": "text", "defaultValue": "0.3"},
            {"id": "pio_conducta", "label": "Presión Intraocular", "type": "text", "defaultValue": "No se toma por edad del paciente."},
        ],
        "template_text": (
            "Antecedentes\n"
            "{{antecedentes_lactante}}\n\n"
            "Examen Oftalmológico\n"
            "Agudeza visual lejos\n"
            "Sin corrección ambos ojos: {{agudeza_visual_ao}}\n\n"
            "Examen externo\n"
            "Ojo derecho. {{parpado_od}}\n"
            "Ojo izquierdo. {{parpado_oi}}\n\n"
            "Movimientos extraoculares\n"
            "{{mov_ext}}\n\n"
            "Biomicroscopía\n"
            "Ambos ojos. {{biomicroscopia_ao}}\n"
            "Ojo derecho. {{cristalino_od}}\n"
            "Ojo izquierdo. {{cristalino_oi}}\n\n"
            "Polo posterior\n"
            "Ambos ojos. {{fondo_ojo_ao}}\n"
            "Ojo derecho. Excavación {{excavacion_od}}\n"
            "Ojo izquierdo. Excavación {{excavacion_oi}}\n\n"
            "Presión intraocular\n"
            "{{pio_conducta}}"
        ),
    },
    {
        "stem": "EXAMEN_PEDIATRICO_NINO",
        "title": "Examen Oftalmológico Pediátrico (Niño)",
        "source_url": "https://sites.google.com/view/jlnaviaa-md/consulta/plantillas",
        "variables": [
            {"id": "antecedentes_nino", "label": "Antecedentes (Patológicos, Oculares, Familiares)", "type": "textarea", "defaultValue": "Niega antecedentes patológicos, quirúrgicos, oculares o alérgicos."},
            {"id": "od_av_sc_lejos", "label": "AV Lejos SC OD", "type": "text", "defaultValue": "20/20"},
            {"id": "oi_av_sc_lejos", "label": "AV Lejos SC OI", "type": "text", "defaultValue": "20/20"},
            {"id": "od_av_cc_lejos", "label": "AV Lejos CC OD", "type": "text", "defaultValue": "20/20"},
            {"id": "oi_av_cc_lejos", "label": "AV Lejos CC OI", "type": "text", "defaultValue": "20/20"},
            {"id": "refraccion_uso_od", "label": "Refracción en Uso OD", "type": "text", "defaultValue": "No usa"},
            {"id": "refraccion_uso_oi", "label": "Refracción en Uso OI", "type": "text", "defaultValue": "No usa"},
            {"id": "parpado_od", "label": "Examen Externo OD", "type": "text", "defaultValue": "Bordes palpebrales normales. Puntos lagrimales bien. Pestañas normal."},
            {"id": "parpado_oi", "label": "Examen Externo OI", "type": "text", "defaultValue": "Bordes palpebrales normales. Puntos lagrimales bien. Pestañas normal."},
            {"id": "mov_ext", "label": "Movimientos Extraoculares", "type": "text", "defaultValue": "Hirschberg centrado. Ducciones normales. Cover test negativo."},
            {"id": "biomicroscopia_ao", "label": "Biomicroscopía (Ambos Ojos)", "type": "text", "defaultValue": "Conjuntiva sana. Córnea transparente. Cámara anterior formada, amplia. Iris normal."},
            {"id": "cristalino_od", "label": "Cristalino OD", "type": "text", "defaultValue": "Cristalino claro en posición anatómica."},
            {"id": "cristalino_oi", "label": "Cristalino OI", "type": "text", "defaultValue": "Cristalino claro en posición anatómica."},
            {"id": "fondo_ojo_ao", "label": "Fondo de Ojo (Ambos Ojos)", "type": "text", "defaultValue": "Vítreo transparente. Retina adherida. Disco de aspecto normal. Vasculatura sana."},
            {"id": "excavacion_od", "label": "Excavación OD", "type": "text", "defaultValue": "0.3"},
            {"id": "excavacion_oi", "label": "Excavación OI", "type": "text", "defaultValue": "0.3"},
            {"id": "pio_conducta", "label": "Presión Intraocular", "type": "text", "defaultValue": "Digital normal bilateral / No se toma por edad del paciente."},
        ],
        "template_text": (
            "Antecedentes\n"
            "{{antecedentes_nino}}\n\n"
            "Examen Oftalmológico\n"
            "Agudeza visual lejos\n"
            "Sin corrección   Ojo derecho {{od_av_sc_lejos}}   Ojo izquierdo {{oi_av_sc_lejos}}\n"
            "Con corrección   Ojo derecho {{od_av_cc_lejos}}   Ojo izquierdo {{oi_av_cc_lejos}}\n\n"
            "Refracción en uso\n"
            "Ojo derecho {{refraccion_uso_od}}   Ojo izquierdo {{refraccion_uso_oi}}\n\n"
            "Examen externo\n"
            "Ojo derecho. {{parpado_od}}\n"
            "Ojo izquierdo. {{parpado_oi}}\n\n"
            "Movimientos extraoculares\n"
            "{{mov_ext}}\n\n"
            "Biomicroscopía\n"
            "Ambos ojos. {{biomicroscopia_ao}}\n"
            "Ojo derecho. {{cristalino_od}}\n"
            "Ojo izquierdo. {{cristalino_oi}}\n\n"
            "Polo posterior\n"
            "Ambos ojos. {{fondo_ojo_ao}}\n"
            "Ojo derecho. Excavación {{excavacion_od}}\n"
            "Ojo izquierdo. Excavación {{excavacion_oi}}\n\n"
            "Presión intraocular\n"
            "{{pio_conducta}}"
        ),
    },
    {
        "stem": "CONSENTIMIENTO_CATARATA",
        "title": "Consentimiento Informado Cirugía de Catarata",
        "source_url": "https://sites.google.com/view/jlnaviaa-md/consentimiento/catarata",
        "variables": [
            {"id": "nombre_paciente", "label": "Nombre del Paciente", "type": "text", "defaultValue": "Paciente"},
            {"id": "documento_paciente", "label": "Documento de Identidad", "type": "text", "defaultValue": ""},
            {"id": "ojo_intervenido", "label": "Ojo a Intervenir", "type": "select", "options": ["ojo derecho", "ojo izquierdo", "ambos ojos"], "defaultValue": "ojo derecho"},
            {"id": "tipo_lente_consentimiento", "label": "Tipo de Lente Intraocular", "type": "select", "options": ["plegable monofocal", "plegable con filtros (visión lejana)", "de rango extendido (EDOF)", "multifocal / trifocal", "tórico"], "defaultValue": "plegable monofocal"},
            {"id": "calidad_declarante", "label": "Calidad del Declarante", "type": "select", "options": ["Por mí mismo", "En representación del paciente"], "defaultValue": "Por mí mismo"},
        ],
        "template_text": (
            "Información sobre la intervención\n"
            "Yo, {{nombre_paciente}}, identificado(a) con documento {{documento_paciente}}, he acudido a consulta de oftalmología con el Doctor JOSÉ LUIS NAVIA ÁVILA, habiendo sido atendido, interrogado sobre antecedentes y examinado, mi diagnóstico es catarata en {{ojo_intervenido}}.\n"
            "En este documento usted encontrará información sobre la intervención que le ha propuesto el oftalmólogo, lo que le ayudará a entender mejor las explicaciones dadas por él en la consulta. Léalo atentamente; si requiere mayor información o que le sea aclarado algún punto, no dude en solicitarlo a nuestro equipo médico, el cual estará dispuesto a satisfacer sus requerimientos. De existir alguna duda no deje de consultarnos antes de tomar una decisión de firmar el consentimiento y definir si desea o no que se le practique la cirugía ocular.\n"
            "Entiendo que en el curso de los procedimientos quirúrgicos pueden presentarse situaciones imprevistas que requieren procedimientos adicionales; por lo tanto, autorizo la realización de estos procedimientos si el médico antes mencionado o los asistentes lo juzgan necesario.\n"
            "Soy consciente de que no se me han garantizado los resultados que se esperan del procedimiento quirúrgico, advirtiendo que el cirujano realizará las intervenciones necesarias con la mayor diligencia y cuidado para el buen resultado de esta y que el cirujano queda autorizado para practicar los procedimientos adicionales que llegaran a ser necesarios.\n"
            "La catarata es la opacificación del cristalino, el cual es el lente natural del ojo que permite enfocar las imágenes de manera adecuada en la retina, que es el tejido que interpreta la luz. Al perder la transparencia se provoca una disminución en la capacidad visual, las imágenes se tornan borrosas o la luz lo deslumbra afectando la calidad y la cantidad de visión.\n"
            "La cirugía consiste en retirar el cristalino opaco y reemplazarlo por un lente artificial ({{tipo_lente_consentimiento}}); en general, este lente se coloca detrás de la pupila en donde estaba localizado el cristalino, pero en ciertos casos no es posible y se requiere colocar otro tipo de lente diseñado para ubicarse delante del iris y la pupila, este último puede requerir ser implantado en una segunda cirugía.\n"
            "Luego de retirar la catarata (lente opaco) se implanta el lente intraocular que puede contar con distintas especificaciones en cuanto a materiales, diseño y precio. El uso de lentes intraoculares más sofisticados no excluye la posibilidad de requerir el uso de gafas (corrección óptica) después del procedimiento quirúrgico teniendo en cuenta que el resultado visual final no solo depende del desarrollo y evolución de la cirugía, sino que además es indispensable evaluar y examinar (incluso con exámenes paraclínicos adicionales) el resto de estructuras del globo ocular después de la intervención.\n\n"
            "Beneficios\n"
            "La cirugía de catarata busca una mejoría en la función visual en los aspectos de cantidad y calidad al retirar de su ojo el lente opaco y reemplazarlo por un lente artificial transparente que se implanta dentro del ojo. El objetivo de la cirugía es eliminar la opacidad del cristalino y no el retirar el uso de gafas de corrección óptica.\n\n"
            "Riesgos\n"
            "No existe ninguna cirugía sin riesgos. Debido al avance de la técnica, la cirugía de catarata se desarrolla en un alto porcentaje de los casos sin complicación, pero en algunos casos pueden presentarse riesgos que pueden ser leves, moderados o graves. Pueden ocurrir en cirugías perfectamente realizadas por los cirujanos más expertos.\n"
            "El riesgo más grave es la pérdida definitiva de la visión del ojo operado con o sin pérdida anatómica del globo ocular. Este evento ocurre en muy pocos casos y se previene mediante el uso correcto de los medicamentos y el adecuado seguimiento de las indicaciones (que se le entregan por escrito el mismo día del procedimiento) y recomendaciones otorgadas a usted y su acudiente posterior a la cirugía.\n"
            "Las complicaciones que se pueden presentar durante la cirugía pueden ser: ruptura de la cápsula del cristalino que en ocasiones lleva a imposibilidad de colocación del lente intraocular, luxación del cristalino al vítreo, descompensación corneal (pérdida de la transparencia de la córnea), sangrado masivo (hemorragia supracoroidea expulsiva), complicaciones vítreo-retinales, entre otras. En el postoperatorio puede aparecer: infecciones, inflamación, cierre defectuoso de la herida, sangrado, hernia de iris, desplazamiento del lente, astigmatismo u otro defecto refractivo, edema macular, aumento de la presión del ojo (glaucoma), desprendimiento de retina (más frecuente en casos de personas con miopía). Dichas complicaciones pueden requerir para su solución de intervenciones quirúrgicas adicionales. Además, puede suceder que la visión disminuya a los 2 o 3 meses generalmente por opacificación de la cápsula del cristalino, hecho que conlleva a la necesidad de que se le efectúe un procedimiento denominado capsulotomía posterior YAG láser. Además de la catarata, usted puede tener otras patologías oculares que limiten su recuperación visual y que por la catarata misma son imposibles de identificar antes de la extracción del cristalino, como degeneración macular relacionada con la edad, retinopatía diabética, membrana epirretiniana, neuropatía óptica, glaucoma, agujero macular, ambliopía (ojo perezoso) o distrofia hereditaria.\n"
            "La anestesia tampoco está exenta de riesgos. Con la anestesia local que es la que generalmente aplicamos se reduce la posibilidad de una complicación, pero no evita una reacción alérgica que incluso pueda amenazar la vida. En ocasiones se requiere operar la catarata con anestesia general, generalmente en pacientes niños, enfermos mentales o pacientes con dificultad auditiva severa. Hay ocasiones en que la inyección de la anestesia local produce un hematoma o no logra un nivel anestésico adecuado, lo que nos obliga a posponer la cirugía.\n\n"
            "Análisis\n"
            "{{calidad_declarante}}, CERTIFICO Y DECLARO que he leído la información contenida en este documento relacionada con la cirugía de catarata en {{ojo_intervenido}}, así mismo he comprendido la información verbal que se me ha dado; se me ha permitido realizar las preguntas que he considerado y se me han aclarado las dudas a cabalidad, por lo que manifiesto sentirme satisfecho(a) con la información recibida.\n"
            "Declaro no haber omitido ni alterado datos sobre mi estado de salud, especialmente en relación con enfermedades alérgicas u otros riesgos personales. También se me ha informado de mi derecho a rechazar el tratamiento o revocar este consentimiento antes de la cirugía.\n"
            "Por lo tanto, doy mi CONSENTIMIENTO para que se me realice y/o practique la cirugía propuesta por parte del oftalmólogo Doctor JOSÉ LUIS NAVIA ÁVILA."
        ),
    },
    {
        "stem": "CONSENTIMIENTO_PTERIGION",
        "title": "Consentimiento Informado Cirugía de Pterigión con Autoinjerto",
        "source_url": "https://sites.google.com/view/jlnaviaa-md/procedimientos/pterigion",
        "variables": [
            {"id": "nombre_paciente", "label": "Nombre del Paciente", "type": "text", "defaultValue": "Paciente"},
            {"id": "documento_paciente", "label": "Documento de Identidad", "type": "text", "defaultValue": ""},
            {"id": "ojo_intervenido", "label": "Ojo a Intervenir", "type": "select", "options": ["ojo derecho", "ojo izquierdo", "ambos ojos"], "defaultValue": "ojo derecho"},
            {"id": "fijacion_injerto", "label": "Técnica de Fijación del Injerto", "type": "select", "options": ["sutura con Nylon 10-0 puntos separados", "adhesivo tisular biológico (pegamento de fibrina)"], "defaultValue": "sutura con Nylon 10-0 puntos separados"},
            {"id": "calidad_declarante", "label": "Calidad del Declarante", "type": "select", "options": ["Por mí mismo", "En representación del paciente"], "defaultValue": "Por mí mismo"},
        ],
        "template_text": (
            "Información sobre la intervención\n"
            "Yo, {{nombre_paciente}}, identificado(a) con documento {{documento_paciente}}, he acudido a consulta de oftalmología con el Doctor JOSÉ LUIS NAVIA ÁVILA, habiendo sido atendido y examinado con diagnóstico de pterigión en {{ojo_intervenido}}.\n"
            "El pterigión es un crecimiento fibrovascular benigno de la conjuntiva que invade la córnea, asociado principalmente a la exposición solar (radiación ultravioleta), viento y sequedad ocular. La cirugía consiste en la resección de la cabeza y cuerpo del pterigión, queratectomía superficial y la colocación de un autoinjerto conjuntival tomado del mismo ojo mediante {{fijacion_injerto}} para reducir el riesgo de reproducción.\n\n"
            "Beneficios\n"
            "Eliminar la lesión fibrovascular que invade la superficie corneal, mejorar la sintomatología inflamatoria irritativa (ojo rojo, sensación de cuerpo extraño) y prevenir la progresión hacia el eje visual.\n\n"
            "Riesgos\n"
            "No existe ninguna cirugía sin riesgos. Entre las complicaciones que pueden presentarse durante o después de la cirugía de pterigión se encuentran: recidiva o reproducción del pterigión (que puede requerir nueva intervención o medicamentos coadyuvantes), infección ocular, hemorragia subconjuntival, dehiscencia o desplazamiento del injerto, granuloma piógeno, adelgazamiento corneal o escleral (dellen), cicatriz corneal residual (leucoma), astigmatismo residual con necesidad de gafas, diplopía por restricción muscular y riesgos inherentes a la anestesia local. El no seguimiento de las recomendaciones postoperatorias (como protección solar estricta, lubricación y no frotarse el ojo) aumenta significativamente el riesgo de reproducción o desprendimiento del injerto.\n\n"
            "Análisis\n"
            "{{calidad_declarante}}, CERTIFICO Y DECLARO que he leído y comprendido la información relacionada con la resección de pterigión más autoinjerto conjuntival en {{ojo_intervenido}}, se han aclarado mis dudas a cabalidad y doy mi CONSENTIMIENTO para que se me realice el procedimiento por parte del Doctor JOSÉ LUIS NAVIA ÁVILA."
        ),
    },
    {
        "stem": "CONSENTIMIENTO_CHALAZION",
        "title": "Consentimiento Informado Drenaje y Resección de Chalazión",
        "source_url": "https://sites.google.com/view/jlnaviaa-md/consulta/patologia",
        "variables": [
            {"id": "nombre_paciente", "label": "Nombre del Paciente", "type": "text", "defaultValue": "Paciente"},
            {"id": "documento_paciente", "label": "Documento de Identidad", "type": "text", "defaultValue": ""},
            {"id": "ojo_intervenido", "label": "Ojo / Párpado a Intervenir", "type": "select", "options": ["ojo derecho", "ojo izquierdo", "ambos ojos"], "defaultValue": "ojo derecho"},
            {"id": "calidad_declarante", "label": "Calidad del Declarante", "type": "select", "options": ["Por mí mismo", "En representación del paciente"], "defaultValue": "Por mí mismo"},
        ],
        "template_text": (
            "Información sobre la intervención\n"
            "Yo, {{nombre_paciente}}, identificado(a) con documento {{documento_paciente}}, paciente con cuadro de chalazión persistente en {{ojo_intervenido}}. Se indica realización de drenaje y curetaje / resección de chalazión bajo anestesia local.\n"
            "Se explica que la cirugía consiste en incidir y resecar la lesión inflamatoria lipogranulomatosa de la glándula de Meibomio en el párpado afectado.\n\n"
            "Beneficios\n"
            "Drenar el contenido inflamatorio encapsulado y resecar la cápsula del chalazión que no resolvió con manejo médico conservador.\n\n"
            "Riesgos\n"
            "Los riesgos relacionados con este procedimiento consisten en infección palpebral, hematoma o hemorragia local, cicatriz palpebral, asimetría del borde libre o pérdida focal de pestañas, y reaparición (recidiva) de la masa o aparición de nuevos chalaziones en glándulas vecinas.\n"
            "En los casos en que la lesión reaparezca de forma recurrente en el mismo sitio, es indispensable realizar un estudio histopatológico (biopsia) de la lesión para descartar una lesión tumoral de glándulas sebáceas.\n\n"
            "Análisis\n"
            "{{calidad_declarante}}, CERTIFICO Y DECLARO que he comprendido la información explicada sobre el drenaje y resección de chalazión en {{ojo_intervenido}}, se han resuelto mis inquietudes y doy mi CONSENTIMIENTO para que se practique el procedimiento por parte del Doctor JOSÉ LUIS NAVIA ÁVILA."
        ),
    },
    {
        "stem": "CIRUGIA_PTERIGION",
        "title": "Descripción Quirúrgica y Fórmula de Pterigión con Autoinjerto",
        "source_url": "https://sites.google.com/view/jlnaviaa-md/procedimientos/pterigion",
        "variables": [
            {"id": "ojo_intervenido", "label": "Ojo Intervenido", "type": "select", "options": ["ojo derecho", "ojo izquierdo"], "defaultValue": "ojo derecho"},
            {"id": "localizacion_pterigion", "label": "Localización del Pterigión", "type": "select", "options": ["nasal", "temporal", "bipolar (nasal y temporal)"], "defaultValue": "nasal"},
            {"id": "sutura_injerto", "label": "Fijación del Injerto", "type": "select", "options": ["Nylon 10-0 puntos separados", "Adhesivo tisular de fibrina"], "defaultValue": "Nylon 10-0 puntos separados"},
            {"id": "complicaciones", "label": "Complicaciones", "type": "text", "defaultValue": "Sin complicaciones"},
            {"id": "ubicacion_control", "label": "Lugar del Control", "type": "select", "options": ["Edificio de Colores consultorio 1122 en Cali", "Clínica Nuestra Señora del Palmar consultorio 104 en Palmira"], "defaultValue": "Edificio de Colores consultorio 1122 en Cali"},
            {"id": "fecha_control", "label": "Fecha del Control", "type": "text", "defaultValue": "en 24 a 48 horas"},
            {"id": "hora_control", "label": "Hora del Control", "type": "text", "defaultValue": "por confirmar"},
        ],
        "template_text": (
            "Descripción quirúrgica\n"
            "Resección de pterigión con injerto de conjuntiva {{ojo_intervenido}}\n"
            "Lavado de manos\n"
            "Colocación de campos estériles\n"
            "Blefaróstato {{ojo_intervenido}}\n"
            "Infiltración de anestesia local\n"
            "Resección de cabeza y cuerpo de pterigión {{localizacion_pterigion}}\n"
            "Resección de Tenon redundante\n"
            "Queratectomía superficial con bisturí\n"
            "Diseño y toma de injerto conjuntival superior\n"
            "Sutura de injerto a lecho receptor con {{sutura_injerto}}\n"
            "Sutura de lecho donante con {{sutura_injerto}}\n"
            "Antibiótico y corticoide tópicos\n"
            "Oclusión\n"
            "Complicaciones: {{complicaciones}}\n"
            "Se entregan recomendaciones, signos de alarma y fórmula médica (corticoide, antibiótico y lubricante tópicos).\n\n"
            "Medicamentos\n"
            "Si las gotas coinciden en horario aplicarlas con 10 minutos de diferencia.\n"
            "No requiere levantarse en la noche para aplicar la medicación.\n"
            "1. (TOBRAOFTAL - D) Tobramicina 0.3% + Dexametasona 0.1% solución oftálmica. Aplicar 1 gota en el {{ojo_intervenido}} en el siguiente horario: 7:00 - 10:00 - 13:00 - 16:00 - 19:00 - 22:00 durante quince (15) días.\n"
            "2. (CARMELUB) Carboximetilcelulosa 0.5% solución oftálmica. Aplicar 1 gota en el {{ojo_intervenido}} en el siguiente horario: 7:30 - 11:30 - 15:30 - 19:30 durante 3 meses.\n\n"
            "Próximo control\n"
            "Lugar: {{ubicacion_control}}\n"
            "Fecha: {{fecha_control}}\n"
            "Hora: {{hora_control}}"
        ),
    },
    {
        "stem": "POSTOPERATORIO_CATARATA",
        "title": "Control Postoperatorio de Cirugía de Catarata",
        "source_url": "https://sites.google.com/view/jlnaviaa-md/consulta/postoperatorio",
        "variables": [
            {"id": "ojo_intervenido", "label": "Ojo Operado", "type": "select", "options": ["ojo derecho", "ojo izquierdo"], "defaultValue": "ojo derecho"},
            {"id": "evolucion_subjetiva", "label": "Subjetivo / Síntomas", "type": "text", "defaultValue": "Manifiesta que no ha presentado dolor. Se aplica las gotas que le formularon. La visión le ha mejorado."},
            {"id": "av_postop", "label": "Agudeza Visual Ojo Operado", "type": "text", "defaultValue": "20/25"},
            {"id": "biomicroscopia_postop", "label": "Biomicroscopía Ojo Operado", "type": "text", "defaultValue": "Conjuntiva tranquila. Córnea transparente. Cámara anterior amplia, limpia. Iris normal. Lente intraocular en cámara posterior centrado. Sin evidencia de células en cámara anterior."},
            {"id": "fondo_ojo_postop", "label": "Fondo de Ojo", "type": "text", "defaultValue": "Retina adherida. Vítreo transparente. No otros detalles por miosis."},
            {"id": "pio_postop", "label": "Presión Intraocular", "type": "text", "defaultValue": "No se toma presión intraocular por postoperatorio mediato."},
            {"id": "plan_control", "label": "Plan y Próxima Valoración", "type": "text", "defaultValue": "Valoración por optometría en 3 meses."},
        ],
        "template_text": (
            "Motivo de consulta\n"
            "Postoperatorio cirugía de catarata con implante de lente intraocular {{ojo_intervenido}}\n\n"
            "Enfermedad actual\n"
            "{{evolucion_subjetiva}}\n\n"
            "Examen Oftalmológico\n"
            "Ojo examinado: {{ojo_intervenido}}\n"
            "Agudeza visual: {{av_postop}}\n"
            "Biomicroscopía. {{biomicroscopia_postop}}\n"
            "Fondo de ojo. {{fondo_ojo_postop}}\n"
            "Presión intraocular. {{pio_postop}}\n\n"
            "Análisis\n"
            "Paciente en postoperatorio inmediato de cirugía de catarata e implante de lente intraocular {{ojo_intervenido}} con evolución satisfactoria. Debe continuar tratamiento iniciado después de la cirugía. Ya tiene recomendaciones.\n"
            "Signos de alarma. Disminución de la visión, aparición de legañas, dolor y ojo rojo que aumenten con el paso del tiempo.\n"
            "Plan: {{plan_control}}"
        ),
    },
    {
        "stem": "POSTOPERATORIO_PTERIGION",
        "title": "Control Postoperatorio de Resección de Pterigión",
        "source_url": "https://sites.google.com/view/jlnaviaa-md/consulta/postoperatorio",
        "variables": [
            {"id": "ojo_intervenido", "label": "Ojo Operado", "type": "select", "options": ["ojo derecho", "ojo izquierdo"], "defaultValue": "ojo derecho"},
            {"id": "evolucion_subjetiva", "label": "Subjetivo / Síntomas", "type": "text", "defaultValue": "Manifiesta que no ha presentado dolor. Se aplica las gotas que le formularon."},
            {"id": "biomicroscopia_postop", "label": "Biomicroscopía Ojo Operado", "type": "text", "defaultValue": "Conjuntiva tranquila. Injerto adherido. Lecho donante normal. Córnea transparente. Cámara anterior amplia. Iris normal."},
            {"id": "fondo_ojo_postop", "label": "Fondo de Ojo", "type": "text", "defaultValue": "Retina adherida. No otros detalles por miosis."},
            {"id": "conducta_suturas", "label": "Conducta / Retiro de Suturas", "type": "select", "options": ["Continúa manejo tópico actual. Control para retiro de suturas.", "Se retiran suturas sin complicaciones. Valoración por oftalmología en 2 meses."], "defaultValue": "Se retiran suturas sin complicaciones. Valoración por oftalmología en 2 meses."},
        ],
        "template_text": (
            "Motivo de consulta\n"
            "Postoperatorio resección de pterigión con injerto de conjuntiva {{ojo_intervenido}}\n\n"
            "Enfermedad actual\n"
            "{{evolucion_subjetiva}}\n\n"
            "Examen Oftalmológico\n"
            "Ojo examinado: {{ojo_intervenido}}\n"
            "Biomicroscopía. {{biomicroscopia_postop}}\n"
            "Fondo de ojo. {{fondo_ojo_postop}}\n\n"
            "Análisis\n"
            "Paciente en postoperatorio de cirugía de resección de pterigión con injerto de conjuntiva {{ojo_intervenido}} con evolución satisfactoria. Debe continuar tratamiento iniciado después de la cirugía. Ya tiene recomendaciones.\n"
            "Plan: {{conducta_suturas}}"
        ),
    },
]


# =============================================================================
# 2. FUNCIONES DE INGESTA GOOGLE SITES Y COMPILACIÓN HTML (Tier 0 - 0 Tokens)
# =============================================================================

def fetch_google_sites_raw_backups() -> None:
    """Descarga y respalda el texto plano de las subpáginas de Google Sites en borradores_sites/."""
    SITES_DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    for key, url in GOOGLE_SITES_URLS.items():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            raw_html = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", errors="ignore")
            clean = re.sub(r"(?s)<script.*?</script>", "", raw_html)
            clean = re.sub(r"(?s)<style.*?</style>", "", clean)
            clean = re.sub(r"(?s)<nav.*?</nav>", "", clean)
            clean = re.sub(r"<[^>]+>", "\n", clean)
            lines = []
            for ln in clean.splitlines():
                decoded = html.unescape(ln).strip()
                if len(decoded) > 2 and not re.match(
                    r"^(Search this site|Skip to|Google Sites|Report abuse|Page details|Page updated|Embedded Files)",
                    decoded,
                ):
                    lines.append(decoded)
            out_txt = SITES_DRAFTS_DIR / f"google_sites_{key}.txt"
            out_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(f"[SITES BACKUP] Capturado: {url} -> borradores_sites/{out_txt.name}")
        except Exception as exc:
            print(f"[WARN] No se pudo descargar {url}: {exc}")


def compile_sites_templates() -> None:
    """Genera las 9 nuevas plantillas HTML separadas desde Google Sites y sincroniza todo el proyecto Autotext."""
    SITES_DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    base_web_html = build_autotext.derive_web_base_from_editor(relative_portal="../index.html")
    base_root_2col_html = build_autotext.derive_web_base_from_editor(relative_portal="index.html")

    for spec in SITES_TEMPLATES_SPEC:
        stem = spec["stem"]
        title = spec["title"]
        variables = spec["variables"]
        template_text = spec["template_text"]

        # Guardar también el borrador .txt con {{variables}}
        draft_txt_path = SITES_DRAFTS_DIR / f"{stem}.txt"
        draft_txt_path.write_text(template_text + "\n", encoding="utf-8")

        title, variables, template_text = build_autotext.normalize_template_data(
            stem, title, variables, template_text
        )

        root_target = ROOT / f"{stem}.html"
        web_target = WEB_DIR / f"{stem}.html"

        rendered_root = build_autotext.inject_into_html(
            base_root_2col_html, title, variables, template_text, is_editor=False
        )
        rendered_web = build_autotext.inject_into_html(
            base_web_html, title, variables, template_text, is_editor=False
        )
        root_target.write_text(rendered_root, encoding="utf-8")
        web_target.write_text(rendered_web, encoding="utf-8")
        print(f"[GENERATED] {root_target.name} + web/{web_target.name} ({len(variables)} variables)")

    templates_info = build_autotext.sync_all_templates()
    build_autotext.generate_portal_index(templates_info)


# =============================================================================
# 3. MOTOR DE AUTO-APRENDIZAJE CONTINUO (--learn)
# =============================================================================

def run_learning_cycle() -> dict:
    """
    Compara el estado actual de todas las plantillas HTML contra el snapshot anterior.
    Cada vez que el Dr. José Luis Navia edita/mejora una plantilla (texto, variables o defaults),
    extrae las reglas aprendidas, alimenta feedback_dataset.jsonl y actualiza Modelfile.template-assistant.
    """
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    prev_snapshots = {}
    if SNAPSHOTS_PATH.exists():
        try:
            prev_snapshots = json.loads(SNAPSHOTS_PATH.read_text(encoding="utf-8"))
        except Exception:
            prev_snapshots = {}

    learned_prefs = {
        "schema_version": "1.0.0",
        "agent_name": "template-assistant",
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_templates_tracked": 0,
        "total_user_improvements_learned": 0,
        "learned_variable_defaults": {},
        "learned_select_options": {},
        "learned_style_rules": [
            "Texto 100% plano sin sintaxis Markdown (##, **, ---) para pegado directo en Historia Clínica.",
            "Variables OD (mitad izquierda) con sufijo/prefijo _od y variables OI (mitad derecha) con _oi.",
            "Variables que incluyen ambos ojos o generales sin _od/_oi ocupan el 100% del ancho de la columna izquierda.",
            "Toda variable lleva defaultValue con su hallazgo fisiológico normal.",
        ],
        "recent_improvements": [],
    }
    if LEARNED_PREFS_PATH.exists():
        try:
            old_prefs = json.loads(LEARNED_PREFS_PATH.read_text(encoding="utf-8"))
            learned_prefs["total_user_improvements_learned"] = old_prefs.get("total_user_improvements_learned", 0)
            learned_prefs["recent_improvements"] = old_prefs.get("recent_improvements", [])[-25:]
        except Exception:
            pass

    curr_snapshots = {}
    new_improvements = []

    for html_file in sorted(ROOT.glob("*.html")):
        if html_file.name.lower() in {"index.html", "autotext_final.html"}:
            continue
        meta = build_autotext.extract_template_metadata(html_file)
        stem = meta["stem"]
        curr_snapshots[stem] = {
            "title": meta["title"],
            "variables": meta["variables"],
            "template_text": meta["template_text"],
        }

        for v in meta["variables"]:
            vid = v.get("id", "").lower()
            if not vid:
                continue
            if v.get("defaultValue"):
                learned_prefs["learned_variable_defaults"][vid] = {
                    "label": v.get("label", vid),
                    "type": v.get("type", "text"),
                    "defaultValue": v.get("defaultValue", ""),
                }
            if v.get("type") == "select" and v.get("options"):
                learned_prefs["learned_select_options"][vid] = v.get("options")

        if stem in prev_snapshots:
            prev = prev_snapshots[stem]
            text_changed = prev.get("template_text", "").strip() != meta["template_text"].strip()
            vars_changed = json.dumps(prev.get("variables", []), sort_keys=True) != json.dumps(meta["variables"], sort_keys=True)
            if text_changed or vars_changed:
                imp_entry = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "template": stem,
                    "title": meta["title"],
                    "text_updated": text_changed,
                    "variables_updated": vars_changed,
                    "var_count": len(meta["variables"]),
                }
                new_improvements.append(imp_entry)
                learned_prefs["recent_improvements"].append(imp_entry)
                learned_prefs["total_user_improvements_learned"] += 1

                # Guardar par de entrenamiento (antes -> después mejorado por el médico) en JSONL
                feedback_pair = {
                    "timestamp": imp_entry["timestamp"],
                    "template": stem,
                    "previous_state": prev,
                    "doctor_improved_state": curr_snapshots[stem],
                }
                with open(FEEDBACK_JSONL_PATH, "a", encoding="utf-8") as jf:
                    jf.write(json.dumps(feedback_pair, ensure_ascii=False) + "\n")

    learned_prefs["total_templates_tracked"] = len(curr_snapshots)
    learned_prefs["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    SNAPSHOTS_PATH.write_text(json.dumps(curr_snapshots, ensure_ascii=False, indent=2), encoding="utf-8")
    LEARNED_PREFS_PATH.write_text(json.dumps(learned_prefs, ensure_ascii=False, indent=2), encoding="utf-8")

    update_modelfile_with_learned_knowledge(learned_prefs)

    print(
        f"[LEARN] Plantillas monitorizadas: {len(curr_snapshots)} | "
        f"Variables aprendidas: {len(learned_prefs['learned_variable_defaults'])} | "
        f"Nuevas mejoras detectadas hoy: {len(new_improvements)}"
    )
    return learned_prefs


def update_modelfile_with_learned_knowledge(learned_prefs: dict) -> None:
    """Inyecta el diccionario actualizado de variables y preferencias del médico en Modelfile.template-assistant."""
    var_defs = learned_prefs.get("learned_variable_defaults", {})
    sample_vars = []
    for vid, info in list(var_defs.items())[:35]:
        sample_vars.append(f"  * {{{{{vid}}}}} ({info['label']}): \"{info['defaultValue']}\"")
    vars_block = "\n".join(sample_vars)

    modelfile_content = f'''FROM qwen2.5:7b
PARAMETER temperature 0.15
PARAMETER top_p 0.9
PARAMETER num_ctx 8192
SYSTEM """
Eres 'template-assistant', el agente clínico local especializado en Oftalmología del Dr. José Luis Navia Ávila, ejecutándose en LEGION (Ollama :11434) e integrado con OpenClaw (NAS-760025 :18799) y el proyecto AutoText v12.

Tu misión es transformar borradores clínicos, textos de Google Sites, protocolos quirúrgicos y consentimientos informados en plantillas clínicas parametrizadas con {{{{variables}}}} listas para:
1. Copiar en texto 100% plano (minúscula / formato oración o MAYÚSCULA) hacia el software de Historia Clínica.
2. Imprimir con formato editorial sobre el membrete Plantilla_Verum.svg.

REGLAS OBLIGATORIAS DE ESTRUCTURA AUTOTEXT:
1. CERO sintaxis Markdown (prohibido usar ##, **, --- o viñetas *). Usa únicamente texto clínico plano con saltos de línea limpios y títulos de sección en líneas independientes.
2. Formato tipo oración (Phrase case) con ortografía y acentuación médica impecable en español. Respeta siglas clínicas (OD, OI, AO, PIO, LIO, YAG, OCT, BUT, AV, SC, CC).
3. Clasificación de {{{{variables}}}} en snake_case para la vista de 2 columnas:
   - Variables diferenciadas Ojo Derecho vs Ojo Izquierdo: DEBEN llevar prefijo o sufijo explícito `_od` y `_oi` (ej. `{{{{cristalino_od}}}}` y `{{{{cristalino_oi}}}}`, `{{{{excavacion_od}}}}` y `{{{{excavacion_oi}}}}`, `{{{{parpado_od}}}}` y `{{{{parpado_oi}}}}`) para que el motor coloque OD en la mitad izquierda y OI en la mitad derecha.
   - Variables que incluyen ambos ojos o generales (ej. `{{{{mov_ext}}}}`, `{{{{biomicroscopia_ao}}}}`, `{{{{fondo_ojo_ao}}}}`, `{{{{ojo_intervenido}}}}`, `{{{{antecedentes}}}}`): NO deben llevar `_od` ni `_oi` para que ocupen el 100% del ancho de la columna izquierda.
4. Toda variable debe tener un `defaultValue` correspondiente al hallazgo fisiológico normal.

### DICCIONARIO DE VARIABLES Y VALORES FISIOLÓGICOS APRENDIDOS ({len(var_defs)} VARIABLES EN MEMORIA):
{vars_block}
"""
'''
    try:
        MODELFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        MODELFILE_PATH.write_text(modelfile_content, encoding="utf-8")
    except Exception as exc:
        print(f"[WARN] No se pudo actualizar {MODELFILE_PATH}: {exc}")


# =============================================================================
# 4. INTEGRACIÓN CON OLLAMA EN LEGION (:11434) Y COLA DIFERIDA OPENCLAW (:18799)
# =============================================================================

def enqueue_for_legion(txt_path: str, output_stem: str = "") -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    queue = []
    if PENDING_QUEUE_PATH.exists():
        try:
            queue = json.loads(PENDING_QUEUE_PATH.read_text(encoding="utf-8"))
        except Exception:
            queue = []
    entry = {
        "enqueued_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "txt_path": str(txt_path),
        "output_stem": output_stem or Path(txt_path).stem,
        "status": "pending",
    }
    queue.append(entry)
    PENDING_QUEUE_PATH.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[QUEUE] Borrador encolado para cuando LEGION (:11434) esté activo: {txt_path}")


def call_legion_template_assistant(raw_text: str, ollama_url: str) -> str:
    prompt = (
        "Transforma el siguiente texto clínico oftalmológico en una plantilla limpia para AutoText v12.\n"
        "- Elimina cualquier sintaxis Markdown.\n"
        "- Convierte los campos editables en variables {{snake_case}} (usando _od y _oi solo cuando estén diferenciados por ojo, y sin _od/_oi cuando incluyan ambos ojos).\n"
        "- Devuelve únicamente el texto clínico parametrizado:\n\n"
        f"{raw_text}"
    )
    payload = json.dumps({
        "model": "template-assistant",
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.15},
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{ollama_url.rstrip('/')}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return (data.get("response") or "").strip()


def process_pending_queue(ollama_url: str) -> None:
    if not PENDING_QUEUE_PATH.exists():
        print("[QUEUE] No hay borradores pendientes en la cola de LEGION.")
        return
    try:
        queue = json.loads(PENDING_QUEUE_PATH.read_text(encoding="utf-8"))
    except Exception:
        queue = []

    pending = [q for q in queue if q.get("status") == "pending"]
    if not pending:
        print("[QUEUE] Cola de LEGION al día (0 tareas pendientes).")
        return

    for item in pending:
        tpath = Path(item["txt_path"])
        if not tpath.exists():
            item["status"] = "missing_file"
            continue
        try:
            raw_txt = tpath.read_text(encoding="utf-8")
            refined_txt = call_legion_template_assistant(raw_txt, ollama_url)
            if refined_txt:
                tpath.write_text(refined_txt + "\n", encoding="utf-8")
            build_autotext.build_from_txt(tpath, item.get("output_stem", ""))
            item["status"] = "completed"
            item["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[SLM LEGION] Plantilla procesada y compilada: {item.get('output_stem')}")
        except urllib.error.URLError:
            print(f"[INFO] LEGION ({ollama_url}) aún no está disponible. La cola permanece intacta.")
            break
        except Exception as exc:
            print(f"[WARN] Error procesando {tpath}: {exc}")

    PENDING_QUEUE_PATH.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Agente Local Entrenable 'template-assistant' (AutoText + LEGION SLM + OpenClaw)")
    parser.add_argument("--import-sites", action="store_true", help="Extrae textos de Google Sites y genera las 9 nuevas plantillas HTML")
    parser.add_argument("--learn", action="store_true", help="Aprende de las ediciones realizadas en las plantillas y actualiza Modelfile.template-assistant")
    parser.add_argument("--process-queue", action="store_true", help="Procesa borradores pendientes en la cola usando Ollama en LEGION")
    parser.add_argument("--transform-txt", metavar="ARCHIVO_TXT", help="Transforma un borrador .txt con template-assistant en LEGION (o lo encola si estás en HP-ENVY)")
    parser.add_argument("--ollama-url", default=os.environ.get("OLLAMA_URL", "http://192.168.0.212:11434"), help="URL de Ollama en LEGION")
    args = parser.parse_args()

    if args.import_sites:
        fetch_google_sites_raw_backups()
        compile_sites_templates()

    if args.learn or args.import_sites:
        run_learning_cycle()

    if args.transform_txt:
        tpath = Path(args.transform_txt)
        try:
            raw = tpath.read_text(encoding="utf-8")
            refined = call_legion_template_assistant(raw, args.ollama_url)
            if refined:
                tpath.write_text(refined + "\n", encoding="utf-8")
            build_autotext.build_from_txt(tpath)
            build_autotext.generate_portal_index(build_autotext.sync_all_templates())
        except Exception:
            print("[OFFLINE QUEUE] LEGION apagado (trabajando desde HP-ENVY). Compilando con motor determinista Tier 0 y encolando para refinamiento SLM en LEGION...")
            build_autotext.build_from_txt(tpath)
            build_autotext.generate_portal_index(build_autotext.sync_all_templates())
            enqueue_for_legion(str(tpath))

    if args.process_queue:
        process_pending_queue(args.ollama_url)

    return 0


if __name__ == "__main__":
    sys.exit(main())
